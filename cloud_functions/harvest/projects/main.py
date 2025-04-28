"""Harvest Projects data pipeline."""

import asyncio
from datetime import datetime
from os import getenv

from data_pipeline_tools.asyncs import get_all_data
from data_pipeline_tools.auth import harvest_headers
from data_pipeline_tools.util import (
    find_and_flatten_columns,
    get_harvest_pages,
    write_to_bigquery,
)
from dateutil.relativedelta import relativedelta

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
        "url": "https://api.harvestapp.com/v2/projects?page=",
        "headers": harvest_headers(project_id, service),
        "dataset_id": getenv("DATASET_ID"),
        "gcp_project": project_id,
        "table_name": getenv("TABLE_NAME"),
        "location": getenv("TABLE_LOCATION"),
        "service": service,
    }


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Run Harvest Clients data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - Harvest Projects"
    config = load_config(project_id, service)

    pages, _ = get_harvest_pages(config["url"], config["headers"])
    projects_df = asyncio.run(get_all_data(config["url"], config["headers"], pages, "projects", batch_size=10))
    projects_df = find_and_flatten_columns(projects_df)

    projects_df["starts_on"] = projects_df["starts_on"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d").date() if x else None)
    projects_df["ends_on"] = projects_df["ends_on"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d").date() if x else None)
    projects_df["completion_percentage"] = projects_df.apply(
        lambda row: None
        if row["ends_on"] is None or row["starts_on"] is None
        else 1
        if row["ends_on"] < datetime.now().date()
        else 0
        if row["starts_on"] > datetime.now().date()
        else (datetime.now().date() - row["starts_on"]) / (row["ends_on"] - row["starts_on"]),
        axis=1,
    )
    projects_df["completed"] = projects_df["completion_percentage"].apply(lambda x: "completed" if x == 1 else "not completed")
    projects_df["completed_months"] = projects_df.apply(lambda row: relativedelta(row["ends_on"], row["starts_on"]).months, axis=1)

    write_to_bigquery(config, projects_df, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({}, None)
