import os

import pandas as pd
import requests

from data_pipeline_tools.auth import hibob_headers
from data_pipeline_tools.util import write_to_bigquery

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not project_id:
    project_id = input("Enter GCP project ID: ")


def load_config(project_id, service) -> dict:
    return {
        "table_name": os.environ.get("TABLE_NAME"),
        "dataset_id": os.environ.get("DATASET_ID"),
        "location": os.environ.get("TABLE_LOCATION"),
        "headers": hibob_headers(project_id, service),
    }


def main(data: dict, context: dict = None):
    service = "Data Pipeline - HiBob Employees"
    config = load_config(project_id, service)
    df = get_employees(config)
    write_to_bigquery(config, df, "WRITE_TRUNCATE")


def get_employees(config: dict):
    cols_to_keep = [
        "email",
        "id",
        "displayName",
        "managerId",
        "secondLevelManagerId",
        "contract",
    ]
    url = "https://api.hibob.com/v1/profiles"
    response = requests.get(url, headers=config["headers"]).json()
    df = pd.DataFrame(response["employees"])
    df["managerId"] = df["work"].apply(lambda x: x.get("manager"))
    df["secondLevelManagerId"] = df["work"].apply(lambda x: x.get("secondLevelManager"))
    df["contract"] = df["work"].apply(lambda x: x.get("site"))
    return df[cols_to_keep]


if __name__ == "__main__":
    main({})
