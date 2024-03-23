import os
from datetime import date

import pandas as pd
import requests

from data_pipeline_tools.auth import hibob_headers
from data_pipeline_tools.util import write_to_bigquery

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or input("Enter GCP project ID: ")
current_year = date.today().year
DATES = [
    date(current_year, 5, 1),
    date(current_year, 7, 1),
    date(current_year, 10, 1),
    date(current_year, 12, 31),
    date.today(),
]


def load_config(project_id, service) -> dict:
    return {
        "table_name": os.environ.get("TABLE_NAME") or "time_off_balances",
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
    service = "Data Pipeline - HiBob Time Off Balances"
    config = load_config(project_id, service)
    # policy_types = get_policy_types(config)
    url = f"https://api.hibob.com/v1/timeoff/requests/changes?since={current_year}-01-01T00%3A00%3A00.000Z&includePending=false"
    response = requests.get(url, headers=config["headers"])
    df = pd.DataFrame(response.json()["changes"])
    # df.drop(
    #     ["employeeEmail", "requestId", "employeeDisplayName", "changeReason"],
    #     axis=1,
    #     inplace=True,
    # )
    # df = df[df["policyTypeDisplayName"].isin(policy_types)]
    # df = df[df["changeType"] == "Created"]
    # df["startDate"] = pd.to_datetime(df["startDate"])
    # df["endDate"] = pd.to_datetime(df["endDate"])

    # results = []
    # for balance_date in DATES:
    #     balance_date = pd.Timestamp(balance_date)
    #     active_requests = df[
    #         (df["startDate"] <= balance_date) & (df["endDate"] >= balance_date)
    #     ]

    #     total_days_per_employee = (
    #         active_requests.groupby("employeeId")["totalDuration"].sum().reset_index()
    #     )
    #     total_days_per_employee["date"] = balance_date
    #     results.append(total_days_per_employee)
    write_to_bigquery(config, df, "WRITE_TRUNCATE")
    # write_to_bigquery(config, pd.concat(results, ignore_index=True), "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({})
