import asyncio
import os

import pandas as pd

from data_pipeline_tools.asyncs import get_all_data
from data_pipeline_tools.auth import harvest_headers
from data_pipeline_tools.util import (
    find_and_flatten_columns,
    get_harvest_pages,
    write_to_bigquery,
)

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not project_id:
    project_id = "tpx-consulting-dashboards"


def load_config(project_id, service) -> dict:
    return {
        "url": "https://api.harvestapp.com/v2/time_entries?page=",
        "headers": harvest_headers(project_id, service),
        "dataset_id": os.environ.get("DATASET_ID"),
        "gcp_project": project_id,
        "table_name": os.environ.get("TABLE_NAME"),
        "location": os.environ.get("TABLE_LOCATION"),
        "service": service,
    }


def main(data: dict, context):
    service = "Data Pipeline - Harvest Timesheets"
    config = load_config(project_id, service)

    pages, entries = get_harvest_pages(config["url"], config["headers"])
    print(f"Total pages: {pages}")
    df = asyncio.run(
        get_all_data(
            config["url"], config["headers"], pages, "time_entries", batch_size=10
        )
    ).reset_index(drop=True)

    df = find_and_flatten_columns(df)
    df["spent_date"] = pd.to_datetime(df["spent_date"], format="%Y-%m-%d")
    df["utilisation"] = df.apply(lambda row: get_utilisation(row), axis=1)
    print(len(df), entries)

    assert abs(len(df) == entries) < 30
    columns_to_drop = []
    df = df.drop(columns=columns_to_drop, errors="ignore")

    write_to_bigquery(config, df, "WRITE_TRUNCATE")


clients = [
    "TPXimpact",
    "TPX Engineering Academy",
    "TPX Engineering Team",
    "Panoply",
    "TPXimpact D&I",
]
tasks = ["Account Development", "Travel Time"]


def get_utilisation(row):
    if row["client_name"] in clients or row["task_name"] in tasks:
        return 0
    else:
        return row["hours"]


if __name__ == "__main__":
    main({}, None)
