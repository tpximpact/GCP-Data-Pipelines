# ruff: noqa: INP001, T201
"""Process Trainline expense reports and upload them to Harvest."""

import sys
from csv import DictWriter
from datetime import date, datetime, timedelta
from os import getenv
from pathlib import Path

import httpx
import pandas as pd
from constants import (
    FUZZ_CONFIDENCE,
    HARVEST_ASSIGNMENT_QUERY,
    NON_BILLABLE_MAPPING,
    TPX_DATA_QUERY,
    TRAINLINE_BILLABLE_ANSWER,
    TRAINLINE_EXPENSE_CATEGORY,
    TRAINLINE_EXPENSE_NOTE,
    TRAINLINE_FOLDER_ID,
    TRAINLINE_REPORT_PATH,
)
from data_pipeline_tools.auth import access_secret_version, harvest_headers
from data_pipeline_tools.drive import GoogleDriveService
from data_pipeline_tools.util import read_from_bigquery, write_to_bigquery
from thefuzz import process

SERVICE = "Data Pipeline - Trainline"
PROJECT_ID = getenv("GOOGLE_CLOUD_PROJECT") or "tpx-consulting-dashboards"
PROCESSING_DATE = date.today() - timedelta(days=2)
SLACK_WEBHOOK_URL = access_secret_version(PROJECT_ID, "SLACK_WEBHOOK_URL")


class ProjectError(Exception):
    """Exception raised for errors while trying to retrieve the project."""


def send_slack_notification(message: str) -> None:
    """Send a notification to Slack using the configured webhook URL.

    Args:
    ----
        message (str): The message to send to Slack

    """
    try:
        response = httpx.post(
            SLACK_WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            json={"text": message},
        )
        print(f"Message sent to Slack: {message}")
        response.raise_for_status()
    except Exception as e:  # noqa: BLE001
        print(f"Error sending Slack notification: {e}")


def get_tpx_query_data(project_id: str, query: str) -> pd.DataFrame:
    """Execute BigQuery and process date columns.

    Args:
    ----
        project_id (str): GCP project ID
        query (str): BigQuery SQL query

    Returns:
    -------
        pd.DataFrame: Query results with processed date columns

    """
    tpx_df = read_from_bigquery(project_id=project_id, query=query)
    tpx_df["start_date"] = pd.to_datetime(tpx_df["start_date"], errors="coerce")
    tpx_df["end_date"] = pd.to_datetime(tpx_df["end_date"], errors="coerce")
    return tpx_df


def write_csv(list_of_dicts: list[dict[str:str]], file_name: str, field_names: list[str] | None = None) -> None:
    """Write list of dictionaries to CSV file.

    Args:
    ----
        list_of_dicts (list[dict[str:str]]): Data to write
        file_name (str): Output file path
        field_names (list[str]): Field names

    """
    if not field_names:
        field_names = list_of_dicts[0].keys()
    with Path.open(file_name, "w") as f:
        writer = DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(list_of_dicts)


def find_monday_friday(date_str: str) -> tuple[str, str]:
    """Find Monday and Friday dates for the week containing given date.

    Args:
    ----
        date_str (str): Input date string

    Returns:
    -------
        tuple[str, str]: Monday and Friday dates in YYYY-MM-DD format

    """
    if not isinstance(date_str, str):
        date_str = str(date_str)[:10]
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except TypeError as e:
        print(e)
        raise
    monday = date - timedelta(days=date.weekday())
    friday = monday + timedelta(days=4)
    return monday.strftime("%Y-%m-%d"), friday.strftime("%Y-%m-%d")


def load_config() -> dict[str:str]:
    """Load Harvest API configuration settings.

    Returns
    -------
        dict[str:str]: Configuration dictionary

    """
    return {
        "base_url": "https://api.harvestapp.com",
        "expense_endpoint": "/v2/expenses",
        "expense_category_endpoint": "/v2/expense_categories",
        "headers": harvest_headers(PROJECT_ID, SERVICE),
        "service": SERVICE,
        "gcp_project": PROJECT_ID,
        "dataset_id": getenv("DATASET_ID") or "trainline",
        "table_name": getenv("TABLE_NAME") or "results",
        "location": getenv("TABLE_LOCATION") or "europe-west2",
    }


def get_project_data(tpx_df: pd.DataFrame, row: pd.Series, name_filter: pd.Series) -> tuple[str, str]:
    """Get billable data for a given row.

    Args:
    ----
        tpx_df (pd.DataFrame): Query results
        row (pd.Series): Input row
        name_filter (pd.Series): Name filter

    Returns:
    -------
        tuple[str, str]: User ID and project ID

    """
    journey_date = row["OutwardLegDate"]
    billable_df = tpx_df[~tpx_df["client_name"].str.contains("TPX")]

    # Filter for exact date
    date_filter = (billable_df["start_date"] == journey_date) & (billable_df["end_date"] == journey_date)
    filtered_df = billable_df.loc[name_filter & date_filter]

    # No match for exact date
    if filtered_df.empty:
        monday, friday = find_monday_friday(journey_date)
        week_filter = (billable_df["start_date"] >= monday) & (billable_df["end_date"] <= friday)
        filtered_df = billable_df.loc[name_filter & week_filter]

        if filtered_df.empty:
            raise ProjectError("no project assigned")

    # Multiple project assignments
    if filtered_df.shape[0] > 1:
        project_list = filtered_df["project_client_name"].unique()
        closest_match = process.extractOne(row["Answer2"], project_list)

        if closest_match[1] > FUZZ_CONFIDENCE:
            filtered_df = filtered_df[filtered_df["project_client_name"] == closest_match[0]]
        else:
            raise ProjectError("no matching project for input")

    match = filtered_df.iloc[0]
    return int(match["user_id"]), int(match["project_id"])


def get_team_data(person: pd.Series) -> tuple[str, str, str]:
    """Get non-billable data for a given person.

    Args:
    ----
        person (pd.Series): Input person

    Returns:
    -------
        tuple[str, str, str]: User ID, project ID, and team name

    """
    try:
        team_name = f"{person['department']} {person['team']}".strip()
        project_id = NON_BILLABLE_MAPPING[team_name]
    except KeyError:
        try:
            team_name = person["department"]
            project_id = NON_BILLABLE_MAPPING[team_name]
        except KeyError:
            print("no mapping for team", person["email"], person["department"], person["team"], sep="\n")
            return "", "", ""
    return int(person["user_id"]), project_id, team_name


def process_expense(
    config: dict[str, str],
    tpx_df: pd.DataFrame,
    assignment_df: pd.DataFrame,
    row: pd.Series,
) -> dict[str:str]:
    """Process an expense row from the Trainline report.

    Args:
    ----
        config (dict[str, str]): Configuration dictionary
        tpx_df (pd.DataFrame): TPX query results
        assignment_df (pd.DataFrame): Assignment query results
        row (pd.Series): Input row

    Returns:
    -------
        dict[str:str]: Expense data

    """
    billable = row["Answer3"] == TRAINLINE_BILLABLE_ANSWER
    internal = "division" in row["Answer3"].lower()
    result = {
        "Date": PROCESSING_DATE,
        "Amount": row["TotalCost"],
        "Units": "",
        "Client": "",
        "Project": "",
        "Category": TRAINLINE_EXPENSE_CATEGORY["name"],
        "Notes": TRAINLINE_EXPENSE_NOTE,
        "First Name": "",
        "Last Name": "",
        "Billable": billable,
    }

    # Use vectorized string matching to filter email
    name_filter = tpx_df["email"].apply(lambda x: x and all(name.lower() in str(x).lower() for name in row["BookerName"].strip().lower().split()))

    if not name_filter.any():
        result["Notes"] = f"no match for '{row['BookerName']}' on forecast"
        return result

    result["First Name"] = tpx_df[name_filter].iloc[0]["first_name"]
    result["Last Name"] = tpx_df[name_filter].iloc[0]["last_name"]

    try:
        if internal:
            user_id, project_id, team_name = get_team_data(tpx_df[name_filter].iloc[0])
        else:
            user_id, project_id = get_project_data(tpx_df[name_filter], row, name_filter)
    except ProjectError as e:
        print(f"Error processing row of {result['First Name']} {result['Last Name']}: {e}")
        result["Notes"] = str(e)
        return result

    if user_id and project_id:
        result["Client"] = "TPXimpact" if internal else tpx_df[tpx_df["project_id"] == project_id]["client_name"].iloc[0]
        result["Project"] = team_name if internal else tpx_df[tpx_df["project_id"] == project_id]["project_name"].iloc[0]
        try:
            if internal:
                assignment_df = assignment_df[(assignment_df["user_id"] == user_id) & (assignment_df["project_id"] == project_id)]
                if assignment_df.empty:
                    try:
                        assign_harvest_project_to_user(config, user_id, project_id)
                    except:  # noqa: E722
                        result["Notes"] = "unable to assign TPX team project"
                        return result
            print(f"Posting £{row['TotalCost']} for {result['First Name']} {result['Last Name']} on {result['Client']} - {result['Project']}")
            post_expense(config, user_id, project_id, row["TotalCost"], billable)
        except Exception as e:  # noqa: BLE001
            result["Notes"] = str(e)
    else:
        result["Notes"] = "unable to retrieve project id"
    return result


def post_expense(
    config: dict[str:str],
    user_id: str,
    project_id: str,
    total_cost: float,
    billable: bool,  # noqa: FBT001
) -> dict[str:str]:
    """Post an expense to Harvest.

    Args:
    ----
        config (dict[str:str]): Configuration dictionary
        user_id (str): User ID
        project_id (str): Project ID
        travel_date (datetime.date): Travel date
        total_cost (float): Total cost
        billable (bool): Is billable

    Returns:
    -------
        dict[str:str]: Response data

    """
    response = httpx.post(
        f"{config['base_url']}{config['expense_endpoint']}",
        headers=config["headers"],
        json={
            "expense_category_id": str(TRAINLINE_EXPENSE_CATEGORY["id"]),
            "user_id": str(int(user_id)),
            "project_id": str(int(project_id)),
            "spent_date": PROCESSING_DATE.strftime("%Y-%m-%d"),
            "total_cost": str(total_cost),
            "notes": "Trainline Business Account - do not reimburse",
            "billable": billable,
        },
    )

    if response.status_code != httpx.codes.CREATED:
        response.raise_for_status()

    return response.json()


def get_trainline_data(path: Path) -> pd.DataFrame:
    """Get Trainline data from a CSV file.

    Args:
    ----
        path (Path): Path to the CSV file

    Returns:
    -------
        pd.DataFrame: Trainline data

    """
    cols_to_keep = ["BookingDate", "BookerName", "OutwardLegDate", "TotalCost", "Answer2", "Answer3"]
    trainline_df = pd.read_csv(path)[cols_to_keep]
    trainline_df["OutwardLegDate"] = pd.to_datetime(trainline_df["OutwardLegDate"], errors="coerce")
    trainline_df["OutwardLegDate"] = trainline_df["OutwardLegDate"].dt.date
    trainline_df["BookingDate"] = pd.to_datetime(trainline_df["BookingDate"], errors="coerce")
    trainline_df["BookingDate"] = trainline_df["BookingDate"].dt.date
    trainline_df = trainline_df[trainline_df["BookingDate"] == PROCESSING_DATE]
    trainline_df = trainline_df[~trainline_df["BookerName"].str.contains("TPX LIMITED")]
    return trainline_df.drop("BookingDate", axis=1).reset_index()


def set_is_active_harvest(config: dict[str:str], *, is_active: bool) -> bool:
    """Set the is_active flag for an expense category on Harvest.

    Args:
    ----
        config (dict[str:str]): Configuration dictionary
        is_active (bool): Is active flag

    Returns:
    -------
        bool: True if the request was successful, False otherwise

    """
    response = httpx.patch(
        f"{config['base_url']}{config['expense_category_endpoint']}/{TRAINLINE_EXPENSE_CATEGORY['id']!s}",
        headers=config["headers"],
        json={
            "is_active": is_active,
        },
    )
    return response.status_code == httpx.codes.OK


def get_trainline_report(gdrive: GoogleDriveService, folder_name: str) -> tuple[Path, str]:
    """Get the Trainline report from Google Drive.

    Args:
    ----
        gdrive (GoogleDriveService): Google Drive service
        folder_name (str): Folder name

    Returns:
    -------
        tuple[Path, str]: Path to the report and report ID

    """
    report_folder = gdrive.find_folder_by_name_in_root(folder_name)
    files = gdrive.list_folder_contents(report_folder["id"])
    if len(files) == 1:
        try:
            return gdrive.download_file(files[0]["id"], TRAINLINE_REPORT_PATH / files[0]["name"]), files[0]["id"]
        except Exception as e:  # noqa: BLE001
            print(e)
    send_slack_notification("Multiple files in Trainline folder, please check manually")
    return None, None


def assign_harvest_project_to_user(config: dict, user_id: int, project_id: int) -> None:
    """Assign a project to a user on Harvest.

    Args:
    ----
        config (dict): The configuration settings.
        user_id (int): The ID of the user.
        project_id (int): The ID of the project.

    Returns:
    -------
        None

    """
    resp = httpx.post(
        f"https://api.harvestapp.com/v2/projects/{project_id!s}/user_assignments",
        headers=config["headers"],
        json={"user_id": str(user_id)},
    )
    if resp.status_code != httpx.codes.CREATED:
        resp.raise_for_status()


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Process the Trainline report.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    sys.exit(-420)
    config = load_config()
    gdrive = GoogleDriveService(PROJECT_ID, TRAINLINE_FOLDER_ID)

    report_path, report_id = get_trainline_report(gdrive, "New")
    results = []
    if report_path:
        send_slack_notification(f"Processing {report_path.name}")
        try:
            gdrive.move_file(report_id, "WIP")
            if set_is_active_harvest(config, is_active=True):
                trainline_df = get_trainline_data(report_path)
                trainline_df.to_csv(Path(f"trainline_{PROCESSING_DATE}.csv"), index=False)
                if not trainline_df.empty:
                    tpx_df = get_tpx_query_data(PROJECT_ID, TPX_DATA_QUERY)
                    assignment_df = read_from_bigquery(project_id=PROJECT_ID, query=HARVEST_ASSIGNMENT_QUERY)
                    results = [process_expense(config, tpx_df, assignment_df, row) for _, row in trainline_df.iterrows()]
        except Exception as e:  # noqa: BLE001
            print(e)
        report_path.unlink(missing_ok=True)
        gdrive.move_file(report_id, "Done")
    set_is_active_harvest(config, is_active=False)
    if results:
        results_df = pd.DataFrame(results)
        results_path = Path(f"results_{PROCESSING_DATE}.csv")
        results_df.to_csv(results_path, index=False)
        gdrive.upload_file(results_path)
        results_path.unlink(missing_ok=True)
        write_to_bigquery(config, results_df, "WRITE_APPEND")


if __name__ == "__main__":
    main()
