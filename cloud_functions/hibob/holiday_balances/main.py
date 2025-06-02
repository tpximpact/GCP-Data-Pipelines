"""Hibob Holiday Balances data pipeline."""

import time
from datetime import datetime
from os import getenv

import pandas as pd
import requests
from data_pipeline_tools.auth import hibob_headers
from data_pipeline_tools.util import write_to_bigquery

project_id = getenv("GOOGLE_CLOUD_PROJECT") or "tpx-consulting-dashboards"

CURRENT_YEAR = datetime.now().year
POLICY_TYPES = []
TPX_POLICY_TYPE = "TPXimpact Holiday"


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
        "table_name": getenv("TABLE_NAME"),
        "dataset_id": getenv("DATASET_ID"),
        "location": getenv("TABLE_LOCATION"),
        "headers": hibob_headers(project_id, service),
    }


def get_employee_ids(config: dict[str:str]) -> list[str]:
    """Get employee IDs.

    Args:
    ----
        config (dict[str:str]): Config

    Returns:
    -------
        list[str]: Employee IDs

    """
    url = "https://api.hibob.com/v1/people/search"

    payload = {
        "fields": ["root.id"],
        "showInactive": False,
        "humanReadable": "REPLACE",
    }
    response = requests.post(
        url,
        headers=config["headers"],
        json=payload,
        timeout=10,
    )
    return [employee["id"] for employee in response.json()["employees"]]


def find_employee_balance(config: dict[str:str], url: str) -> dict[str:str]:
    """Find employee balance on Hibob.

    Args:
    ----
        config (dict[str:str]): Config
        url (str): Partially formatted URL

    """
    for policy_type in POLICY_TYPES:
        response = requests.get(
            url.format(policy_type=policy_type),
            headers=config["headers"],
            timeout=10,
        )
        try:
            if response.json():
                return response.json()
        except Exception as e:  # noqa: BLE001
            print(response)
            print(e)
    print(f"Unable to get balance for {url}")
    return {}


def get_policy_types(config: dict[str:str]) -> list[str]:
    """Get policy types from Hibob.

    Args:
    ----
        config (dict[str:str]): Config

    Returns:
    -------
        list[str]: Policy types

    """
    url = "https://api.hibob.com/v1/timeoff/policy-types"
    response = requests.get(url, headers=config["headers"], timeout=10)
    return [policy_type.strip() for policy_type in response.json()["policyTypes"] if "holiday" in policy_type.lower()]


def get_employee_balance(employee_id: str, config: dict[str:str]) -> dict[str:str]:
    """Get employee balance from Hibob.

    Args:
    ----
        employee_id (str): Employee ID
        config (dict[str:str]): Config

    Returns:
    -------
        dict[str:str]: Employee balance

    """
    url = "https://api.hibob.com/v1/timeoff/employees/{employee_id}/balance?policyType={policy_type}&date={year}-12-31"
    response = requests.get(
        url.format(employee_id=employee_id, policy_type=TPX_POLICY_TYPE, year=CURRENT_YEAR),
        headers=config["headers"],
        timeout=10,
    )
    if int(response.headers["X-RateLimit-Remaining"]) == 1:
        time.sleep(int(response.headers["X-RateLimit-Reset"]) - time.time() + 1)
    try:
        if not response.json():
            return find_employee_balance(config, url.format(employee_id=employee_id, year=CURRENT_YEAR, policy_type="{policy_type}"))
    except:  # noqa: E722
        print(response.text)
        return {}
    return response.json()


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Run Hibob Holiday Balances data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - HiBob Holiday Balances"
    config = load_config(project_id, service)
    global POLICY_TYPES  # noqa: PLW0603
    POLICY_TYPES = get_policy_types(config)
    POLICY_TYPES.remove(TPX_POLICY_TYPE)
    balances = [get_employee_balance(employee_id, config) for employee_id in get_employee_ids(config)]
    write_to_bigquery(
        config,
        pd.DataFrame([balance for balance in balances if balance]),
        "WRITE_TRUNCATE",
    )


if __name__ == "__main__":
    main({})
