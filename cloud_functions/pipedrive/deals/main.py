import os

import pandas as pd
from pipedrive.client import Client

from data_pipeline_tools.auth import pipedrive_access_token
from data_pipeline_tools.util import flatten_columns, write_to_bigquery

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not project_id:
    # project_id = input("Enter GCP project ID: ")
    project_id = "tpx-consulting-dashboards"


def update_keys(dict_list, keys_to_update, new_keys):
    broken_keys = set()
    for dictionary in dict_list:
        for old_key, new_key in zip(keys_to_update, new_keys):
            try:
                dictionary[new_key] = dictionary.pop(old_key)
            except:  # noqa: E722
                broken_keys.add((old_key, new_key))
        break
    print("Unable to change following keys:", broken_keys)
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
    if isinstance(key, str):
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

    columns_to_drop = [] + unnamed_columns
    flat_deals = flat_deals.drop(columns=columns_to_drop, errors="ignore")

    write_to_bigquery(config, flat_deals, "WRITE_TRUNCATE")


unnamed_columns = [
    "d59c50f571c97868459bbe177d905d0781b8a804",
    "d59c50f571c97868459bbe177d905d0781b8a804_until",
    "3a6c5997697f11bbe73689dbe9aaa5f69c0faa82",
    "32edde49694df51cf2982654f36f5cb52008d4da",
    "5f56744a273ce8704a635cb5f3ebde5bc8a54781",
    "814c4f2332094b7d3b6bf62579f78abdfae9c294",
    "09527c3c334ecbd9bd32ba53b1e5cadeb9762c9f",
    "850ab5d504b8339ff9a4b7177ee213c40331a49b",
    "3311098397ae1850ddca8b56fc678c6125ed4234",
    "1029b2fb1d2cb42c0c2c65d08a26c68f93fcc9b1",
    "ce1f05eff8b26acbb129eae9b3b24da8fbe74270",
    "8bbbee28949069f6a09dc1aacffe0b062ddc73f1",
    "3d41079d03d6eac7eeabaa234cd4003b3799ae08",
    "861ab267cb7b7714c78946126490efa06110884c",
    "33d19105d4d7f9f4a4c088328ae10077187b2c17",
    "621c96615c86135bf02467cc50b43a06fdc62f7f",
    "a1d12a1b7bfbae608a7a08580b434d4229cc1db3",
    "7320534be22ea6a1d818a18429b55297c20694ab",
    "e8af0665daef3ec666c1afc139a5edc37f8c580d",
    "5a85c9d0d45af12177eabf8f7da8a79a461547b0",
    "930b9d09f86157df72c4207d09efe6b96b48d214",
    "c49d10be5537184cddb6131a8f5a2ed9b4330214",
    "6595c5a2c7dbbdc2c5c6a4d1516d65619c4c889c",
    "6074f0410663fe2806fd372ba7c6b2d65032229d",
    "e1aa11a751f668680ef0293de518318090b8895d",
    "cf59356a9fc8dd40f7934a976c31674073db4f26",
    "0edc4610ad2c8dd7080317d7f7fadb17b8dd59ce",
    "26c04796d1dcebf1293bcb943898423b7b9aa2b9",
    "26c04796d1dcebf1293bcb943898423b7b9aa2b9_timezone_id",
    "a2cd06693b9ce5eec13b37bdc8cb7304737f434e",
    "2b3260c57f594487c65d0cfcb53d947b08fa27ab",
    "2b3260c57f594487c65d0cfcb53d947b08fa27ab_timezone_id",
    "fbcb1018ed3569f6aebb2b67028b50a4b32fca18",
    "a160725adb7b70930cf033498a3fad986b1b1a87",
    "1cdbdaef231969d15a13748661f470072770bc9c",
    "959b76038505be28c049cad44f8fceb20bb69da8",
    "056b7555faefa7ffd7377c1482810a8398bdc99e",
    "c3d80b61133faf4ef343b1a1c51a0a5246403d61",
    "da8dbe69f9dee92c5dcba51d34012b29ac116643",
    "f73594b17f047aeed6593363ea4b014419d51bfb",
    "42d6cab97031715b252d5c0bc3915a7c8c7f6f97",
    "ffb999fedfebfc6769f35d60d19c09a5c90d7df6",
    "92589bddbe8ea11903a9829a6321d0ad817f6062",
    "5d8f7aa6d5b1ac706a262d5999cc829b954dee53",
    "89c56aed47181d9d35547fdf1cc845bc9ffde1c4",
    "330800d78f805aaec517606d353825cc1449cdc9",
    "330800d78f805aaec517606d353825cc1449cdc9_currency",
    "d99b0620288f33950c422ec559cf7a86271b4ce5",
    "23dc681c3c4a2eef21bafbe8aff072b6aa390cce",
    "6c44c04934cdd9bdb618185dc0a419c5d438a539",
    "4cb1fa6b4027c3e18f9674e5fced7b15ea3123b3",
    "bcec97807ec2c50709d145bbde33eadb4ee85932",
    "4a2c6c0968b91d4bcaf60c908b150d948c4635bc",
    "5ae3c9a87ba3f6213bd5ec05652dcba45b83677a",
    "98202f3b95ddcc718d54f1f38b8661d3ace88015",
    "02da6bf4ced0a7a716ddb95abfaa2d7bbf003289",
    "02da6bf4ced0a7a716ddb95abfaa2d7bbf003289_currency",
    "23263de853af083f5c03ca71ff57df129407b566",
    "1d0b8a8636de2246d23aaee4bf0ca3d9a683711a",
    "dd2c75545b5de157bcf0476d6919cc538521b6bc",
    "fc105f31716342de9ffc501657258ddca583c31a",
    "6bae05dfd0cd766244c9d785de4fb4954b391b28",
    "085ebcabb156e86724897f36947e44be3714fd18",
    "d469ac2ec46e09cd4335c9f8b23dd018c1ee1775",
    "762c74099f40711a347547b0055747a74ca362db",
    "c91dcf7504619751be7dd1a92268de665d15f585",
    "2383073d746496763df2889d6c6c9d2a87a63c1c",
    "0f591a719a85926d63d3f31ec81387f1d6f50cf7",
]
if __name__ == "__main__":
    main({}, None)
