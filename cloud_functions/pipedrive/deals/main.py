import os

import pandas as pd
from pipedrive.client import Client

from data_pipeline_tools.auth import pipedrive_access_token
from data_pipeline_tools.util import flatten_columns, write_to_bigquery

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not project_id:
    # project_id = input("Enter GCP project ID: ")
    project_id = "tpx-cheetah"


def update_keys(dict_list, keys_to_update, new_keys):
    for dictionary in dict_list:
        for old_key, new_key in zip(keys_to_update, new_keys):
            dictionary[new_key] = dictionary.pop(old_key)
    return dict_list


def load_config(project_id, service) -> dict:
    return {
        "auth_token": pipedrive_access_token(project_id),
        "dataset_id": os.environ.get("DATASET_ID"),
        "gcp_project": project_id,
        "table_name": os.environ.get("TABLE_NAME"),
        "location": os.environ.get("TABLE_LOCATION"),
        "service": service,
    }


def get_option_from_key(key: str, options) -> str:
    if type(key) == str:
        if key.isnumeric():
            option = options[options["id"] == int(key)]["label"].values
            if len(option) > 0:
                return option[0]
            if len(key) > 0:
                return f"{key} Not Found ?!?"
    return key


def main(data: dict, context):
    service = "Data Pipeline - Pipedrive Deals"
    config = load_config(project_id, service)

    client = Client(domain="https://companydomain.pipedrive.com/")

    client.set_api_token(config["auth_token"])
    print("Pipedrive client created")
    done = False
    deals = []
    start = 0  # 0 is the first deal
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

    deal_fields_resp = client.deals.get_deal_fields()["data"] + client.deals.get_deal_fields(params={"start": 100})["data"]
    column_names = pd.DataFrame(
        [
            {
                "name": column["name"],
                "key": column["key"],
                "options": column.get("options"),
            }
            for column in deal_fields_resp
        ]
    )

    unnamed_columns = column_names[column_names["key"].str.len() > 30]
    optioned_columns = column_names[column_names["options"].notnull()]
    update_keys(
        deals, unnamed_columns["key"].to_list(), unnamed_columns["name"].to_list()
    )
    deals_df = pd.DataFrame(deals).rename(
        columns=lambda x: x.replace(
            " ",
            "_",
        ).lower()
    )
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
    flat_deals = flat_deals
    print("Deals flattened")

    for _, item in optioned_columns.iterrows():

        flat_deals[item["name"].replace(" ", "_").lower()] = flat_deals[
            item["name"].replace(" ", "_").lower()
        ].apply(lambda x: get_option_from_key(x, pd.DataFrame(item["options"])))

    flat_deals = flat_deals.drop(
        columns=[
            "bid_clarifications_due_by_time",
            "timezone_of_bid_clarifications_due_by_time",
            "timezone_of_bid/proposal_deadline_time",
        ]
    )
    print("Deal options updated")

    write_to_bigquery(config, flat_deals, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({}, None)
