"""Hibob Time Off data pipeline."""

import copy
import json
from datetime import datetime, timedelta
from os import getenv

import httpx
import pandas as pd
from data_pipeline_tools.auth import hibob_headers
from data_pipeline_tools.util import write_to_bigquery

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
        "table_name": getenv("TABLE_NAME"),
        "dataset_id": getenv("DATASET_ID"),
        "location": getenv("TABLE_LOCATION"),
        "headers": hibob_headers(project_id, service),
    }


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Run Hibob Time Off data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - HiBob Time Off"
    config = load_config(project_id, service)
    write_to_bigquery(config, get_holidays(config, httpx.Client()), "WRITE_TRUNCATE")


def get_holidays(config: dict, client: httpx.Client) -> pd.DataFrame:
    """Get holidays from Hibob.

    Args:
    ----
        config (dict[str:str]): Config
        client (httpx.Client): HTTP client

    """

    def expand_holidays_rows(df: pd.DataFrame) -> pd.DataFrame:
        # When an assignment is entered, it can be put in for a single day or multiple.
        # For entries spanning across multiple days, this function converts to single day entries and returns the dataframe.
        edited_rows = []
        for _, row in df[df["startDate"] != df["endDate"]].iterrows():
            # get the times
            end_date = datetime.strptime(row["endDate"], "%Y-%m-%d")
            start_date = datetime.strptime(row["startDate"], "%Y-%m-%d")

            dates = get_weekdays(start_date, end_date)

            first_row = copy.copy(row)
            if len(dates) > 1:
                first_row["endPortion"] = "all_day"
                middle_rows = copy.copy(row)
                middle_rows["startPortion"] = "all_day"
                middle_rows["endPortion"] = "all_day"
                for date in dates[1:-1]:
                    edited_rows.append(set_dates_in_row(copy.copy(middle_rows), date))  # noqa: PERF401
                last_row = copy.copy(row)
                last_row["startPortion"] = "all_day"
                edited_rows.append(set_dates_in_row(copy.copy(last_row), dates[-1]))
            edited_rows.append(set_dates_in_row(first_row, dates[0]))

        return pd.concat([df[df["startDate"] == df["endDate"]], pd.DataFrame(edited_rows)])

    def find_hours(row: pd.Series) -> int:
        if row["startPortion"] == "all_day" and row["endPortion"] == "all_day":
            return 8
        return 4

    start_timestamp = (datetime.now() - timedelta(days=10000)).strftime("%Y-%m-%d")
    end_timestamp = (datetime.now() + timedelta(days=10000)).strftime("%Y-%m-%d")

    url = f"https://api.hibob.com/v1/timeoff/whosout?from={start_timestamp}&to={end_timestamp}&includeHourly=false&includePrivate=true"

    resp = json.loads(client.get(url, headers=config["headers"], timeout=None).text)

    df = expand_holidays_rows(pd.DataFrame(resp["outs"]))  # noqa: PD901

    df["holiday_hours"] = df.apply(lambda row: find_hours(row), axis=1)
    df["holiday_days"] = df["holiday_hours"] / 8
    df["allocation_hours"] = 0
    df["allocation_days"] = 0
    df["billable"] = False
    df["entry_type"] = "holiday"
    df["project_id"] = 509809
    return df.drop(
        [
            "startPortion",
            "endPortion",
        ],
        axis=1,
    ).rename(
        columns={
            "endDate": "end_date",
            "startDate": "start_date",
            "requestId": "id",
            "employeeDisplayName": "name",
        },
    )


def set_dates_in_row(row: pd.Series, date: datetime) -> pd.Series:
    """Set the start and end dates in a row to a specific date.

    Args:
    ----
        row (pd.Series): Row to update
        date (datetime): Date to set

    Returns:
    -------
        pd.Series: Updated row

    """
    string_date = datetime.strftime(date, "%Y-%m-%d")
    row["startDate"] = string_date
    row["endDate"] = string_date
    return row


def get_weekdays(start_date: datetime, end_date: datetime) -> list:
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
        start = start + timedelta(days=1)
    return dates_list


if __name__ == "__main__":
    main({})
