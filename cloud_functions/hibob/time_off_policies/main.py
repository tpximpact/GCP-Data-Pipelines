"""Hibob Time Off Policies data pipeline."""

from os import getenv

import pandas as pd
import requests
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
        "table_name": getenv("TABLE_NAME") or "time_off_policies",
        "dataset_id": getenv("DATASET_ID") or "hibob_raw",
        "location": getenv("TABLE_LOCATION") or "europe-west2",
        "headers": hibob_headers(project_id, service),
    }


def get_policy_types(config: dict[str:str]) -> list[str]:
    """Get list of available policy types.

    Args:
    ----
        config (dict[str:str]): Config

    Returns:
    -------
        list[str]: List of policy types

    """
    url = "https://api.hibob.com/v1/timeoff/policy-types"
    response = requests.get(url, headers=config["headers"], timeout=10)
    return [policy_type.strip() for policy_type in response.json()["policyTypes"]]


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Run Hibob Time Off Policies data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - HiBob Time Off Policies"
    config = load_config(project_id, service)
    policies = []
    for policy_type in get_policy_types(config):
        policy_url = f"https://api.hibob.com/v1/timeoff/policies/names?policyTypeName={policy_type}"
        response = requests.get(policy_url, headers=config["headers"], timeout=10)
        for policy_name in response.json()["policies"]:
            url = f"https://api.hibob.com/v1/timeoff/policies?policyName={policy_name}"
            response = requests.get(url, headers=config["headers"], timeout=10)
            if not response.json().get("error"):
                policies.append(response.json())

    write_to_bigquery(config, pd.DataFrame(policies)[["name", "allowance"]], "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({})
