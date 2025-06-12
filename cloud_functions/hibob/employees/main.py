"""Hibob Employees data pipeline."""

from os import getenv

import pandas as pd
import requests
from data_pipeline_tools.auth import hibob_headers
from data_pipeline_tools.util import write_to_bigquery

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
        "table_name": getenv("TABLE_NAME"),
        "dataset_id": getenv("DATASET_ID"),
        "location": getenv("TABLE_LOCATION"),
        "headers": hibob_headers(project_id, service),
    }


def main(data: dict = None, context: dict = None) -> None:  # noqa: ARG001, RUF013
    """Run Hibob Employees data pipeline.

    Arguments are not used, but required by the Cloud Function framework.

    Args:
    ----
        data (dict): Data dictionary
        context (dict): Context dictionary

    """
    service = "Data Pipeline - HiBob Employees"
    config = load_config(project_id, service)
    write_to_bigquery(config, pd.DataFrame(get_employees(config)), "WRITE_TRUNCATE")


def get_employees(config: dict[str, str]) -> list[dict[str, str]]:
    """Get all employees from Hibob.

    Args:
    ----
        config (dict[str, str]): Config

    Returns:
    -------
        list[dict[str, str]]: Employees

    """
    url = "https://api.hibob.com/v1/people/search"
    bob_fields = [
        "root.id",
        "root.email",
        "root.displayName",
        "root.fullName",
        "work.manager",
        "work.secondLevelManager",
        "work.siteId",
        "work.startDate",
        "work.customColumns.column_1712065124837",  # department
        "work.customColumns.column_1712065102576",  # team
        "work.customColumns.column_1687442781137",  # job level
        "work.title",
        "work.employeeIdInCompany",
        "work.reportsToIdInCompany",
    ]

    response = requests.post(
        url,
        headers=config["headers"],
        json={
            "fields": bob_fields,
            "humanReadable": "APPEND",
            "showInactive": True,
        },
        timeout=10,
    )

    employees = []
    for employee in response.json()["employees"]:
        employee_data = {
            "email": employee["email"],
            "id": employee["id"],
            "displayName": employee["displayName"],
            "managerId": employee["work"]["manager"],
            "secondLevelManagerId": employee["work"]["secondLevelManager"],
            "contract": employee["humanReadable"]["work"]["siteId"],
            "startDate": employee["work"]["startDate"],
            "title": employee["work"]["title"],
            "employeeIdInCompany": employee["work"]["employeeIdInCompany"],
            "reportsToIdInCompany": employee["work"]["reportsToIdInCompany"],
        }
        try:
            employee_data["department"] = employee["humanReadable"]["work"]["customColumns"]["column_1712065124837"]
        except KeyError:
            employee_data["department"] = ""
        try:
            employee_data["team"] = employee["humanReadable"]["work"]["customColumns"]["column_1712065102576"]
        except KeyError:
            employee_data["team"] = ""
        try:
            employee_data["jobLevel"] = employee["humanReadable"]["work"]["customColumns"]["column_1687442781137"]
        except KeyError:
            employee_data["jobLevel"] = ""
        employees.append(employee_data)

    return employees


if __name__ == "__main__":
    main({})
