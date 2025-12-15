"""Harvest User Project Assignments data pipeline."""

import asyncio
from http import HTTPStatus
from os import getenv

import aiohttp
import pandas as pd
from data_pipeline_tools.auth import harvest_headers
from data_pipeline_tools.util import (
    read_from_bigquery,
    write_to_bigquery,
)

project_id = getenv("GOOGLE_CLOUD_PROJECT") or "tpx-consulting-dashboards"

HARVEST_USER_QUERY = f"""
SELECT id
FROM `{project_id}.Harvest_Raw.users`
WHERE is_active IS TRUE
"""  # noqa: S608
MAX_RETRIES = 3


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
        "url": "https://api.harvestapp.com/v2/users/{user_id}/cost_rates",
        "headers": harvest_headers(project_id, service),
        "dataset_id": getenv("DATASET_ID"),
        "gcp_project": project_id,
        "table_name": getenv("TABLE_NAME"),
        "location": getenv("TABLE_LOCATION"),
        "service": service,
    }


async def get_user_cost_rate_with_retry(
    session: aiohttp.ClientSession,
    user_id: str,
    url: str,
    headers: dict[str, str],
    rate_limit_state: dict,
) -> list[dict]:
    """Get user cost rate with retry logic for rate limiting.

    Args:
    ----
        session (aiohttp.ClientSession): HTTP session
        user_id (str): User ID
        url (str): URL template
        headers (dict[str, str]): Headers to use for the request
        rate_limit_state (dict): Shared state dict with "lock" and "printed" as keys

    Returns:
    -------
        list[dict]: List of cost rate objects from the API response

    Raises:
    ------
        aiohttp.ClientResponseError: If max retries exceeded

    """
    last_response = None
    for attempt in range(MAX_RETRIES):
        async with session.get(url.format(user_id=user_id), headers=headers, timeout=30) as response:
            last_response = response
            if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                retry_after = int(response.headers.get("Retry-After", 60))
                wait_time = retry_after + (2**attempt)

                async with rate_limit_state["lock"]:
                    if not rate_limit_state["printed"]:
                        print(f"429, waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}")
                        rate_limit_state["printed"] = True

                await asyncio.sleep(wait_time)

                async with rate_limit_state["lock"]:
                    rate_limit_state["printed"] = False

                continue
            if response.status == HTTPStatus.OK:
                response_data = await response.json()
                cost_rates = response_data.get("cost_rates", [])
                return [{"user_id": user_id, **rate} for rate in cost_rates]
            response.raise_for_status()

    raise aiohttp.ClientResponseError(
        request_info=last_response.request_info if last_response else None,
        history=last_response.history if last_response else (),
        status=HTTPStatus.TOO_MANY_REQUESTS,
        message=f"429 after {MAX_RETRIES} retries",
    )


async def get_user_cost_rates(
    user_ids: list[str],
    url: str,
    headers: dict[str, str],
    batch_size: int = 10,
) -> pd.DataFrame:
    """Get user cost rates for a list of user IDs.

    Args:
    ----
        user_ids (list[str]): List of user IDs
        url (str): URL to get user cost rates from
        headers (dict[str, str]): Headers to use for the request
        batch_size (int): Number of requests to process concurrently

    Returns:
    -------
        pd.DataFrame: DataFrame containing user cost rates

    """
    semaphore = asyncio.Semaphore(batch_size)
    all_cost_rates = []
    rate_limit_state = {"lock": asyncio.Lock(), "printed": False}

    async with aiohttp.ClientSession() as session:

        async def fetch_with_semaphore(user_id: str) -> list[dict]:
            async with semaphore:
                return await get_user_cost_rate_with_retry(session, user_id, url, headers, rate_limit_state)

        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i : i + batch_size]
            print(f"Processing batch {i // batch_size + 1} ({len(batch)} users)")
            tasks = [fetch_with_semaphore(user_id) for user_id in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"Error fetching user cost rate: {result}")
                elif isinstance(result, list):
                    all_cost_rates.extend(result)

            if i + batch_size < len(user_ids):
                await asyncio.sleep(0.5)

    return pd.DataFrame(all_cost_rates)


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Run Harvest User Cost Rates data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - Harvest User Cost Rates"
    config = load_config(project_id, service)
    user_ids = read_from_bigquery(project_id, HARVEST_USER_QUERY)["id"].to_list()

    user_cost_rates_df = asyncio.run(get_user_cost_rates(user_ids, config["url"], config["headers"]))
    write_to_bigquery(config, user_cost_rates_df, "WRITE_TRUNCATE")


if __name__ == "__main__":
    main()
