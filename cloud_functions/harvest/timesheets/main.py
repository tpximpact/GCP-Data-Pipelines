"""Harvest Timesheets data pipeline."""

import asyncio
from os import getenv

import pandas as pd
from data_pipeline_tools.asyncs import get_all_data
from data_pipeline_tools.auth import harvest_headers
from data_pipeline_tools.util import (
    find_and_flatten_columns,
    get_harvest_pages,
    write_to_bigquery,
)

project_id = getenv("GOOGLE_CLOUD_PROJECT") or "tpx-consulting-dashboards"

CLIENTS = [
    "TPXimpact",
    "TPX Engineering Academy",
    "TPX Engineering Team",
    "Panoply",
    "TPXimpact D&I",
    "TPXimpact Central",
]
TASKS = [
    "Account Development",
    "Account Management",
    "Delivery - Non Billable",
    "Delivery Overview",
    "Executive Sponsorship",
    "Growth Sponsorship",
    "Travel Time",
]


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
        "url": "https://api.harvestapp.com/v2/time_entries?page=",
        "headers": harvest_headers(project_id, service),
        "gcp_project": project_id,
        "dataset_id": getenv("DATASET_ID"),
        "table_name": getenv("TABLE_NAME"),
        "location": getenv("TABLE_LOCATION"),
        "service": service,
    }


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Run Harvest Timesheets data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """

    def get_utilisation(row: pd.Series) -> float:
        return 0 if row["client_name"] in CLIENTS or row["task_name"] in TASKS else row["hours"]

    service = "Data Pipeline - Harvest Timesheets"
    config = load_config(project_id, service)

    pages, _ = get_harvest_pages(config["url"], config["headers"])
    timesheets_df = asyncio.run(get_all_data(config["url"], config["headers"], pages, "time_entries", batch_size=10))
    timesheets_df = find_and_flatten_columns(timesheets_df)
    timesheets_df["spent_date"] = pd.to_datetime(timesheets_df["spent_date"], format="%Y-%m-%d")
    timesheets_df["utilisation"] = timesheets_df.apply(lambda row: get_utilisation(row), axis=1)

    write_to_bigquery(config, timesheets_df, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({}, None)
