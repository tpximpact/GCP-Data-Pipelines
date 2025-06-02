"""Forecast Placeholders data pipeline."""

from os import getenv

import pandas as pd
from data_pipeline_tools.forecast_tools import forecast_client, unwrap_forecast_response
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
    """Run Forecast Placeholders data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - Forecast Placeholders"
    config = load_config(project_id, service)
    client = forecast_client(project_id)
    placeholders_resp = unwrap_forecast_response(client.get_placeholders())

    write_to_bigquery(config, pd.DataFrame(placeholders_resp), "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({})
