"""Forecast Clients data pipeline."""

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
    """Run Forecast Assignments Filled data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - Forecast People"
    config = load_config(project_id, service)
    client = forecast_client(project_id)
    people_resp = unwrap_forecast_response(client.get_people())

    people_df = pd.DataFrame(people_resp)

    people_df["working_days"] = people_df["working_days"].apply(lambda working_days: list(working_days.values()).count(True))
    people_df["weekly_capacity"] = people_df["weekly_capacity"] / (3600 * 8)

    people_df["external"] = people_df["roles"].apply(lambda row: "associate" in row)

    columns_to_drop = []
    people_df = people_df.drop(columns=columns_to_drop, errors="ignore")
    write_to_bigquery(config, people_df, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({})
