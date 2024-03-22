import asyncio
import os
from datetime import date
from typing import Any

import httpx
import pandas as pd
import requests

from data_pipeline_tools.auth import hibob_headers
from data_pipeline_tools.util import read_from_bigquery, write_to_bigquery

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not project_id:
    project_id = input("Enter GCP project ID: ")

AUTH = "Basic U0VSVklDRS0xMjIyOTozMWtTQUtlZjlGbkQxNDFucUtLOFVyNHhYelBDN29kc09FWDVhWXNR"
QUERY = f"SELECT id FROM `{project_id}.hibob_raw.employees`"


def load_config(project_id, service) -> dict:
    return {
        "table_name": os.environ.get("TABLE_NAME"),
        "dataset_id": os.environ.get("DATASET_ID"),
        "location": os.environ.get("TABLE_LOCATION"),
        "headers": hibob_headers(project_id, service),
    }


def main(data: dict, context: dict = None):
    service = "Data Pipeline - HiBob Time Off"
    config = load_config(project_id, service)
    policy_types = get_policy_types(config)
    employee_ids = read_from_bigquery(project_id, QUERY)

    balances = []
    for employee_id in employee_ids["id"].to_list():
        for policy_type in policy_types:
            balance = get_employee_balance(config, employee_id, policy_type)
            if balance:
                balances.append(balance)

    df = pd.DataFrame(balances)
    write_to_bigquery(config, df, "WRITE_TRUNCATE")


def get_policy_types(config: dict) -> list[str]:
    url = "https://api.hibob.com/v1/timeoff/policy-types"
    response = requests.get(
        url,
        headers={
            "accept": "application/json",
            "authorization": AUTH,
        },
    )

    return [
        policy_type
        for policy_type in response.json()["policyTypes"]
        if "holiday" in policy_type.lower()
    ]


def get_employee_balance(
    config: dict, employee_id: str, policy_type: str
) -> dict[str:Any]:
    url = f"https://api.hibob.com/v1/timeoff/employees/{employee_id}/balance?policyType={policy_type}&date={date.today().isoformat()}"
    response = requests.get(
        url,
        headers={
            "accept": "application/json",
            "authorization": AUTH,
        },
    )
    if response.json():
        return response.json()
    return {}


if __name__ == "__main__":
    data = {}  # Your input data here
    context = {}  # Your context here, if any
    asyncio.run(main(data, context))
