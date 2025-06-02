"""Forecast Projects data pipeline."""

from datetime import datetime
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
    """Run Forecast Projects data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """

    def get_artificial_projects() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id": 999999,
                    "name": "blank",
                    "color": "white",
                    "code": None,
                    "notes": None,
                    "start_date": None,
                    "end_date": None,
                    "harvest_id": None,
                    "archived": False,
                    "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "updated_by_id": None,
                    "client_id": None,
                    "tags": [],
                },
            ],
        )

    service = "Data Pipeline - Forecast Projects"
    config = load_config(project_id, service)

    projects_resp = unwrap_forecast_response(forecast_client(project_id).get_projects())
    projects_df = pd.DataFrame(projects_resp)
    final_df = pd.concat([projects_df, get_artificial_projects()], ignore_index=True)

    columns_to_drop = []
    final_df = final_df.drop(columns=columns_to_drop, errors="ignore")

    write_to_bigquery(config, final_df, "WRITE_TRUNCATE")
    print("Done")


if __name__ == "__main__":
    main({})
