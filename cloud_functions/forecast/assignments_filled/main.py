"""Forecast Assignments Filled data pipeline."""

import calendar
from datetime import datetime
from os import getenv

import pandas as pd
from data_pipeline_tools.holiday import get_uk_holidays
from data_pipeline_tools.util import read_from_bigquery, write_to_bigquery

project_id = getenv("GOOGLE_CLOUD_PROJECT") or "tpx-consulting-dashboards"
FY_START_MONTH = 4
FRIDAY = 4
FIRST_YEAR = 2022
CURRENT_YEAR = datetime.now().year - (1 if datetime.now().month < FY_START_MONTH else 0)


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
    """Run Forecast Assignments Filled data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - Forecast Assignments Filled"
    config = load_config(project_id, service)
    max_year = CURRENT_YEAR + 2

    bank_holidays = [date.strftime("%Y-%m-%d") for year in range(FIRST_YEAR, max_year) for date in get_uk_holidays(year)["spent_date"]]

    date_range = sorted(set(get_weekdays_in_fy(2)) - set(bank_holidays))

    forecast_query = f"""
    SELECT * FROM `{config['gcp_project']}.Forecast_Raw.assignments`
    WHERE DATE(start_date) > "{FIRST_YEAR}-03-31"
    AND DATE(start_date) < "{max_year}-03-31"
    """  # noqa: S608
    forecast_df = read_from_bigquery(project_id, forecast_query)

    hibob_people_query = f"""
    SELECT id FROM `{config['gcp_project']}.Forecast_Raw.people`
    WHERE archived = false
    """  # noqa: S608
    people_df = read_from_bigquery(project_id, hibob_people_query)

    entries = []
    for person_id in people_df["id"].to_list():
        temp_df = forecast_df[forecast_df["person_id"] == person_id]
        already_filled_dates = temp_df["start_date"].to_list()
        blank_dates = [x for x in date_range if x not in already_filled_dates]

        for index, day in enumerate(blank_dates):
            entries.append(
                {
                    "id": index,
                    "start_date": day,
                    "end_date": day,
                    "allocation": 14400.0,
                    "notes": None,
                    "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "updated_by_id": 9999999,
                    "project_id": 999999,
                    "person_id": person_id,
                    "repeated_assignment_set_id": None,
                    "active_on_days_off": False,
                    "hours": 8.0,
                    "days": 1,
                },
            )

    write_to_bigquery(config, pd.concat([forecast_df, pd.DataFrame(entries)]), "WRITE_TRUNCATE")


def get_weekdays_in_fy(number_of_years: int = 1) -> list[str]:
    """Get all weekdays for a given number of financial years starting from the current one.

    Args:
    ----
        number_of_years (int): Number of financial years to include

    Returns:
    -------
        list[str]: List of weekdays

    """

    def get_weekdays(year: int, month: int) -> list[str]:
        return [
            datetime(year, month, day).strftime("%Y-%m-%d")
            for day in range(1, calendar.monthrange(year, month)[1] + 1)
            if calendar.weekday(year, month, day) <= FRIDAY
        ]

    months = [datetime(CURRENT_YEAR + i // 12, i % 12 + 1, 1) for i in range(FY_START_MONTH - 1, FY_START_MONTH - 1 + number_of_years * 12)]
    return [day for month in months for day in get_weekdays(month.year, month.month)]


if __name__ == "__main__":
    main({})
