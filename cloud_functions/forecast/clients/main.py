"""Forecast Clients data pipeline."""

from os import getenv

import pandas as pd
from data_pipeline_tools.forecast_tools import forecast_client
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
    service = "Data Pipeline - Forecast Clients"
    config = load_config(project_id, service)
    write_to_bigquery(
        config,
        pd.DataFrame([client._json_data for client in forecast_client(project_id).get_clients()]),  # noqa: SLF001
        "WRITE_TRUNCATE",
    )


if __name__ == "__main__":
    main({})
