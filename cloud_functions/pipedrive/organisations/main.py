"""Pipedrive Organisations data pipeline."""

from os import getenv

import pandas as pd
from data_pipeline_tools.auth import pipedrive_access_token
from data_pipeline_tools.util import write_to_bigquery
from pipedrive.client import Client

project_id = getenv("GOOGLE_CLOUD_PROJECT") or "tpx-consulting-dashboards"


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
    """Run Pipedrive Organisations data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """

    def get_option_from_key(key: str, options: pd.DataFrame) -> str:
        if isinstance(key, str) and key.isnumeric():
            option = options[options["id"] == int(key)]["label"]
            if len(option) > 0:
                return option.to_numpy()[0]
            if len(key) > 0:
                return f"{key} Not Found ?!?"
        return key

    def update_keys(dict_list: list[dict], keys_to_update: list[str], new_keys: list[str]) -> list[dict]:
        for dictionary in dict_list:
            for old_key, new_key in zip(keys_to_update, new_keys, strict=True):
                if old_key in dictionary:
                    dictionary[new_key.replace(" ", " ").lower()] = dictionary.pop(old_key)
        return dict_list

    service = "Data Pipeline - Pipedrive Organisations"
    config = load_config(project_id, service)

    client = Client(domain="https://companydomain.pipedrive.com/")

    client.set_api_token(config["auth_token"])
    print("Pipedrive client created")

    done = False
    organisations = []
    start = 0  # 0 is the first deal
    while not done:
        print(f"Getting organisations from start: {start}")
        organisations_resp = client.organizations.get_all_organizations(params={"start": start})
        if not organisations_resp["success"]:
            raise Exception("Error retrieving organisations")
        organisations += organisations_resp["data"]
        if not organisations_resp["additional_data"]["pagination"]["more_items_in_collection"]:
            done = True
        else:
            start = organisations_resp["additional_data"]["pagination"]["next_start"]

    print("organisations retrieved")

    org_fields_resp = client.organizations.get_organization_fields()
    if not org_fields_resp["success"]:
        raise Exception("unsuccessful")
    org_fields = pd.DataFrame(
        [
            {
                "name": c["name"],
                "key": c["key"],
                "options": c.get("options"),
            }
            for c in org_fields_resp["data"]
        ],
    )

    optioned_columns = org_fields[org_fields["options"].notna()]
    orgs_df = pd.DataFrame(update_keys(organisations, org_fields["key"], org_fields["name"])).rename(
        columns=lambda x: x.replace(
            " ",
            "_",
        ).lower(),
    )
    for _, item in optioned_columns.iterrows():
        print(item["name"])
        orgs_df[item["name"].replace(" ", "_").lower()] = orgs_df[item["name"].replace(" ", "_").lower()].apply(
            lambda x: get_option_from_key(x, pd.DataFrame(item["options"])),  # noqa: B023
        )

    columns_to_drop = []
    orgs_df = orgs_df.drop(columns=columns_to_drop, errors="ignore")

    write_to_bigquery(config, orgs_df, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main({}, {})
