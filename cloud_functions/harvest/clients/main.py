"""Harvest Clients data pipeline."""

import asyncio
from os import getenv

from data_pipeline_tools.asyncs import get_all_data
from data_pipeline_tools.auth import harvest_headers
from data_pipeline_tools.util import (
    find_and_flatten_columns,
    get_harvest_pages,
    write_to_bigquery,
)

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
        "url": "https://api.harvestapp.com/v2/clients?page=",
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
    service = "Data Pipeline - Harvest Clients"
    config = load_config(project_id, service)

    pages, _ = get_harvest_pages(config["url"], config["headers"])
    clients_df = asyncio.run(get_all_data(config["url"], config["headers"], pages, "clients", batch_size=10))

    write_to_bigquery(config, find_and_flatten_columns(clients_df), "WRITE_TRUNCATE")


if __name__ == "__main__":
    main()
