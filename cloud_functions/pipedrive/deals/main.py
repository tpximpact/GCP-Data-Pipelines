"""Pipedrive Deals data pipeline."""

import json
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
        if key is None:
            return None
        try:
            key_int = int(str(key))
        except (ValueError, TypeError):
            return key
        option = options[options["id"] == key_int]["label"].to_numpy()
        if len(option) > 0:
            return option[0]
        return str(key_int)

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
        
    ]

    flat_deals = flatten_columns(deals_df, nested_columns)
    print("Deals flattened")
    
    if "person_id_email" not in flat_deals.columns and "person_id" in deals_df.columns:
        flat_deals["person_id_email"] = deals_df["person_id"].apply(
            lambda v: (v.get("email")[0]["value"] if isinstance(v, dict) and v.get("email") else None)
            
        )
    if "person_id_phone" not in flat_deals.columns and "person_id" in deals_df.columns:
        flat_deals["person_id_phone"] = deals_df["person_id"].apply(
            lambda v: (v.get("phone")[0]["value"] if isinstance(v, dict) and v.get("phone") else None)
        )
        extracted_emails = flat_deals["person_id_email"].dropna().head(3).tolist()

    for _, item in optioned_columns.iterrows():
        name_col = get_column_name(item["name"])
        key_col = item["key"]
        options_df = pd.DataFrame(item["options"])

        target_col = None
        if name_col in flat_deals.columns:
            target_col = name_col
        elif key_col in flat_deals.columns:
            target_col = key_col
        else:
            print(f"Warning: Option field missing. name='{item['name']}' key='{key_col}' looked for '{name_col}' or '{key_col}'")
            continue

        flat_deals[target_col] = flat_deals[target_col].apply(lambda x: get_option_from_key(x, options_df))

        
        if target_col == key_col and name_col not in flat_deals.columns:
            flat_deals = flat_deals.rename(columns={key_col: name_col})

    flat_deals = flat_deals.drop(
        columns=[
            "bid_clarifications_due_by_time",
            "timezone_of_bid_clarifications_due_by_time",
            "timezone_of_bid/proposal_deadline_time",
            "contracting_entity_(if_different_from_end_client)",  
        ],
        errors="ignore",
    )

    columns_to_drop = unnamed_columns["key"].to_list()
    flat_deals = flat_deals.drop(columns=columns_to_drop, errors="ignore")

    write_to_bigquery(config, flat_deals, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({}, None)
