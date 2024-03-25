import os

import pandas as pd
import requests

from data_pipeline_tools.auth import hibob_headers
from data_pipeline_tools.util import write_to_bigquery

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or input("Enter GCP project ID: ")


def load_config(project_id, service) -> dict:
    return {
        "table_name": os.environ.get("TABLE_NAME") or "time_off_policies",
        "dataset_id": os.environ.get("DATASET_ID") or "hibob_raw",
        "location": os.environ.get("TABLE_LOCATION") or "europe-west2",
        "headers": hibob_headers(project_id, service),
    }


def get_policy_types(config: dict[str:str]) -> list[str]:
    url = "https://api.hibob.com/v1/timeoff/policy-types"
    response = requests.get(url, headers=config["headers"])
    return [
        policy_type.strip()
        for policy_type in response.json()["policyTypes"]
        if "holiday" in policy_type.lower()
    ]


def main(data: dict, context: dict = None):
    service = "Data Pipeline - HiBob Time Off Policies"
    config = load_config(project_id, service)
    policies = []
    for policy_type in get_policy_types(config):
        url = f"https://api.hibob.com/v1/timeoff/policies?policyName={policy_type}"
        response = requests.get(url, headers=config["headers"])
        if not response.json().get("error"):
            policies.append(response.json())
    df = pd.DataFrame(policies)
    df = df[["name", "allowance"]]

    write_to_bigquery(config, df, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({})
