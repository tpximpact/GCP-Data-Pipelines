"""Forecast Assignments data pipeline."""

import copy
from datetime import datetime, timedelta
from os import getenv

import pandas as pd
from data_pipeline_tools.forecast_tools import forecast_client, unwrap_forecast_response
from data_pipeline_tools.util import write_to_bigquery

START_DATE = datetime(2021, 4, 1)

project_id = getenv("GOOGLE_CLOUD_PROJECT") or "tpx-consulting-dashboards"


def load_config(project_id: str, service: str) -> dict[str, str]:
    """Load config for the pipeline.

    Args:
    ----
        project_id (str): Project ID
        service (str): Service name

    Returns:
    -------
        dict[str, str]: Config

    """
    return {
        "dataset_id": getenv("DATASET_ID"),
        "gcp_project": project_id,
        "table_name": getenv("TABLE_NAME"),
        "location": getenv("TABLE_LOCATION"),
        "service": service,
    }


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Run Forecast Assignments data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - Forecast Assignments (Active and Inactive)"
    config = load_config(project_id, service)
    client = forecast_client(project_id)

    start_date = START_DATE

    assignments_list = []
    while start_date < datetime.today() + timedelta(days=800):
        end_date = start_date + timedelta(days=179)
        assignments_active = unwrap_forecast_response(
            client.get_assignments(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            ),
        )
        assignments_inactive = unwrap_forecast_response(
            client.get_assignments(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                state="inactive",
            ),
        )
        start_date += timedelta(days=180)
        assignments_list += assignments_active + assignments_inactive

    assignments_df = pd.DataFrame(assignments_list)
    if len(assignments_list) > 0:
        forecast_assignment_data = expand_assignments_rows(assignments_df)

        forecast_assignment_data = forecast_assignment_data[pd.to_datetime(forecast_assignment_data["end_date"]) > START_DATE]

        forecast_assignment_data["hours"] = forecast_assignment_data["allocation"] / 3600
        forecast_assignment_data["days"] = forecast_assignment_data["hours"] / 8

    write_to_bigquery(config, forecast_assignment_data.drop_duplicates(), "WRITE_TRUNCATE")


def expand_assignments_rows(ass_df: pd.DataFrame) -> pd.DataFrame:
    """Expand assignments spanning multiple days to single day assignments.

    Args:
    ----
        ass_df (pd.DataFrame): DataFrame of assignments

    Returns:
    -------
        pd.DataFrame: DataFrame with single day assignments

    """
    if "placeholder_id" in ass_df.columns:
        ass_df = ass_df.drop(columns=["placeholder_id"])
    rows_to_edit = ass_df[ass_df["start_date"] != ass_df["end_date"]]
    single_assignment_rows = ass_df[ass_df["start_date"] == ass_df["end_date"]]

    edited_rows = [
        set_dates_in_row(copy.copy(row), weekday)
        for _, row in rows_to_edit.iterrows()
        for weekday in get_weekdays(
            datetime.strptime(row["start_date"], "%Y-%m-%d"),
            datetime.strptime(row["end_date"], "%Y-%m-%d"),
        )
    ]

    return pd.concat([single_assignment_rows, pd.DataFrame(edited_rows)])


def get_weekdays(start_date: datetime, end_date: datetime) -> list[datetime]:
    """Get list of weekdays between start and end dates.

    Args:
    ----
        start_date (datetime): Start date
        end_date (datetime): End date

    Returns:
    -------
        list: List of weekday dates

    """
    start = copy.copy(start_date)
    dates_list = []
    while start <= end_date:
        if start.weekday() < 5:  # noqa: PLR2004
            dates_list.append(start)
        start += timedelta(days=1)
    return dates_list


def set_dates_in_row(row: pd.Series, date: datetime) -> pd.Series:
    """Set the start and end dates in a row to a specific date.

    Args:
    ----
        row (pd.Series): Row to convert
        date (datetime): Date to set

    Returns:
    -------
        pd.Series: Updated row

    """
    date_string = datetime.strftime(date, "%Y-%m-%d")
    row["start_date"] = date_string
    row["end_date"] = date_string
    return row


if __name__ == "__main__":
    main({})
