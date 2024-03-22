import asyncio
import logging
import os
from datetime import date
from typing import Any

import backoff
import httpx
import pandas as pd

from data_pipeline_tools.auth import hibob_headers
from data_pipeline_tools.util import read_from_bigquery, write_to_bigquery

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("httpx")
logger.setLevel(logging.DEBUG)

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or input("Enter GCP project ID: ")
current_year = date.today().year
AUTH = "Basic U0VSVklDRS0xMjIyOTozMWtTQUtlZjlGbkQxNDFucUtLOFVyNHhYelBDN29kc09FWDVhWXNR"
QUERY = f"SELECT id, contract FROM `{project_id}.hibob_raw.employees`"
DATES = [
    date(current_year, 5, 1),
    date(current_year, 7, 1),
    date(current_year, 10, 1),
    date(current_year, 12, 31),
    date.today(),
]


def load_config(project_id, service) -> dict:
    return {
        "table_name": os.environ.get("TABLE_NAME"),
        "dataset_id": os.environ.get("DATASET_ID"),
        "location": os.environ.get("TABLE_LOCATION"),
        "headers": hibob_headers(project_id, service),
    }


@backoff.on_exception(backoff.expo, httpx.HTTPStatusError, max_time=30)
async def get_employee_balance(
    config: dict,
    semaphore: asyncio.Semaphore,
    employee_id: str,
    policy_type: str,
    balance_date: date = date.today(),
) -> dict[str, Any]:
    url = f"https://api.hibob.com/v1/timeoff/employees/{employee_id}/balance?policyType={policy_type}&date={balance_date.isoformat()}"
    async with semaphore, httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={
                "accept": "application/json",
                "authorization": AUTH,
            },
        )
        response.raise_for_status()
        if response.status_code == 200 and response.json():
            return response.json()
        return {}


async def main(data: dict, context: dict = None):
    service = "Data Pipeline - HiBob Time Off Balances"
    config = load_config(project_id, service)
    policy_types = ["TPXimpact Holiday"]
    employees = read_from_bigquery(project_id, QUERY)

    semaphore = asyncio.Semaphore(10)
    balances = []
    for _, employee in employees.iterrows():
        if "TPX" in employee["contract"]:
            for policy_type in policy_types:
                tasks = []

                for balance_date in DATES:
                    tasks.append(
                        get_employee_balance(
                            config,
                            semaphore,
                            employee["id"],
                            policy_type,
                            balance_date,
                        )
                    )
                balances.extend(await asyncio.gather(*tasks))
                asyncio.sleep(0.5)

    balances = await asyncio.gather(*tasks)
    df = pd.DataFrame([balance for balance in balances if balance])
    write_to_bigquery(config, df, "WRITE_TRUNCATE")


if __name__ == "__main__":
    asyncio.run(main({}))
