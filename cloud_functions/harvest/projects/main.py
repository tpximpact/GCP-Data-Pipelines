import asyncio
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

from data_pipeline_tools.asyncs import get_all_data
from data_pipeline_tools.auth import harvest_headers
from data_pipeline_tools.util import (
    find_and_flatten_columns,
    get_harvest_pages,
    write_to_bigquery,
)

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not project_id:
    project_id = input("Enter GCP project ID: ")


def load_config(project_id, service) -> dict:
    return {
        "url": "https://api.harvestapp.com/v2/projects?page=",
        "headers": harvest_headers(project_id, service),
        "dataset_id": os.environ.get("DATASET_ID"),
        "gcp_project": project_id,
        "table_name": os.environ.get("TABLE_NAME"),
        "location": os.environ.get("TABLE_LOCATION"),
        "service": service,
    }


def main(data: dict, context):
    service = "Data Pipeline - Harvest Projects"
    config = load_config(project_id, service)

    pages, entries = get_harvest_pages(config["url"], config["headers"])
    print(f"Total pages: {pages}")
    df = asyncio.run(
        get_all_data(config["url"], config["headers"], pages, "projects", batch_size=10)
    )
    df = find_and_flatten_columns(df)
    df["starts_on"] = df["starts_on"].apply(
        lambda x: datetime.strptime(x, "%Y-%m-%d").date() if x else None
    )
    df["ends_on"] = df["ends_on"].apply(
        lambda x: datetime.strptime(x, "%Y-%m-%d").date() if x else None
    )
    df["completion_percentage"] = df.apply(
        lambda row: None
        if row["ends_on"] is None
        else 1
        if row["ends_on"] < datetime.now().date()
        else 0
        if row["starts_on"] > datetime.now().date()
        else (datetime.now().date() - row["starts_on"])
        / (row["ends_on"] - row["starts_on"]),
        axis=1,
    )

    df["completed"] = df["completion_percentage"].apply(
        lambda x: "completed" if x == 1 else "not completed"
    )

    df["completed_months"] = df.apply(
        lambda row: relativedelta(row["ends_on"], row["starts_on"]).months, axis=1
    )

    assert len(df) == entries
    columns_to_drop = []
    df = df.drop(columns=columns_to_drop, errors="ignore")

    write_to_bigquery(config, df, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({}, None)
