"""Pipedrive Deals data pipeline."""

from os import getenv

import pandas as pd
from data_pipeline_tools.auth import pipedrive_access_token
from data_pipeline_tools.util import flatten_columns, write_to_bigquery
from pipedrive.client import Client

project_id = getenv("GOOGLE_CLOUD_PROJECT") or "tpx-consulting-dashboards"

UNNAMED_KEY_MIN_LENGTH = 30
COLUMN_MAPPING = {
    "Source origin": "origin",
    "Source channel": "channel",
}


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
        "auth_token": pipedrive_access_token(project_id),
        "dataset_id": getenv("DATASET_ID"),
        "gcp_project": project_id,
        "table_name": getenv("TABLE_NAME"),
        "location": getenv("TABLE_LOCATION"),
        "service": service,
    }


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013, C901
    """Run Pipedrive Deals data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """

    def update_keys(dictionary: dict, keys_to_update: list, new_keys: list) -> dict:
        broken_keys = set()
        for old_key, new_key in zip(keys_to_update, new_keys, strict=True):
            try:
                dictionary[new_key] = dictionary.pop(old_key)
            except:  # noqa: E722
                broken_keys.add((old_key, new_key))
        print("Unable to change following keys:", broken_keys)
        return dictionary

    def get_column_name(item_name: str) -> str:
        return COLUMN_MAPPING.get(item_name, item_name.replace(" ", "_").lower())

    def get_option_from_key(key: str, options: pd.DataFrame) -> str:
        if isinstance(key, str) and key.isnumeric():
            option = options[options["id"] == int(key)]["label"].to_numpy()
            if len(option) > 0:
                return option[0]
            if len(key) > 0:
                return f"{key} Not Found ?!?"
        return key

    service = "Data Pipeline - Pipedrive Deals"
    config = load_config(project_id, service)

    client = Client(domain="https://companydomain.pipedrive.com/")
    client.set_api_token(config["auth_token"])

    done = False
    deals = []
    start = 0
    while not done:
        print(f"Getting deals from start: {start}")
        deals_resp = client.deals.get_all_deals(params={"start": start})
        if not deals_resp["success"]:
            raise Exception("Error retrieving deals")
        deals += deals_resp["data"]
        if not deals_resp["additional_data"]["pagination"]["more_items_in_collection"]:
            done = True
        else:
            start = deals_resp["additional_data"]["pagination"]["next_start"]

    print("Deals retrieved")

    deal_fields_resp = (
        client.deals.get_deal_fields()["data"]
        + client.deals.get_deal_fields(params={"start": 100})["data"]
        + client.deals.get_deal_fields(params={"start": 200})["data"]
    )
    column_names = pd.DataFrame(
        [
            {
                "name": column["name"],
                "key": column["key"],
                "options": column.get("options"),
            }
            for column in deal_fields_resp
        ],
    )

    unnamed_columns = column_names[column_names["key"].str.len() > UNNAMED_KEY_MIN_LENGTH]
    optioned_columns = column_names[column_names["options"].notna()]
    updated_deals = [update_keys(deal, unnamed_columns["key"].to_list(), unnamed_columns["name"].to_list()) for deal in deals]
    deals_df = pd.DataFrame(updated_deals).rename(columns=lambda x: str(x).replace(" ", "_").lower())
    nested_columns = [
        "creator_user_id",
        "user_id",
        "org_id",
        "person_id",
        "bid_manager",
        "person_id_email",
        "person_id_phone",
    ]

    flat_deals = flatten_columns(deals_df, nested_columns)
    print("Deals flattened")

    for _, item in optioned_columns.iterrows():
        column_name = get_column_name(item["name"])

        if column_name in flat_deals.columns:
            flat_deals[column_name] = flat_deals[column_name].apply(lambda x: get_option_from_key(x, pd.DataFrame(item["options"])))  # noqa: B023
        else:
            print(f"Warning: Column {column_name} does not exist in flat_deals")

    flat_deals = flat_deals.drop(
        columns=[
            "bid_clarifications_due_by_time",
            "timezone_of_bid_clarifications_due_by_time",
            "timezone_of_bid/proposal_deadline_time",
        ],
    )

    columns_to_drop = unnamed_columns["key"].to_list()
    flat_deals = flat_deals.drop(columns=columns_to_drop, errors="ignore")

    write_to_bigquery(config, flat_deals, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({}, None)
