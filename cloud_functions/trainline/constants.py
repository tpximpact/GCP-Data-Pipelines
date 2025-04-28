# ruff: noqa: INP001
"""Configuration for the Trainline automation."""

from pathlib import Path

TRAINLINE_FOLDER_ID = "1FtiHL-4KCoBNiDlYuCRD0B7hagKKk_d2"
TRAINLINE_REPORT_PATH = Path.cwd()

TRAINLINE_BILLABLE_ANSWER = "Billable Project Travel"

FUZZ_CONFIDENCE = 75

TRAINLINE_EXPENSE_CATEGORY = {
    "id": 10720705,
    "name": "Travel - Business Account: Trainline",
}
TRAINLINE_EXPENSE_NOTE = "Trainline Business Account - do not reimburse"

TPX_DATA_QUERY = """
SELECT h.id as `project_id`, CONCAT(h.client_name,"|",h.name) as `project_client_name`,
  LOWER(pp.email) as `email`, a.start_date, a.end_date, pp.harvest_user_id as `user_id`,
  b.department, b.team, h.client_name as `client_name`, pp.first_name, pp.last_name,
  h.name as `project_name`
FROM `tpx-consulting-dashboards.Forecast_Raw.assignments` a
JOIN `tpx-consulting-dashboards.Forecast_Raw.projects` p
ON a.project_id = p.id
JOIN `tpx-consulting-dashboards.Forecast_Raw.people` pp
ON a.person_id = pp.id
JOIN `tpx-consulting-dashboards.Harvest_Raw.projects` h
ON p.harvest_id = h.id
JOIN `tpx-consulting-dashboards.hibob_raw.employees` b
ON LOWER(pp.email) = LOWER(b.email)
WHERE 1=1
AND pp.email IS NOT NULL
"""

HARVEST_ASSIGNMENT_QUERY = """
SELECT user_id, project_id FROM `Harvest_Raw.user_project_assignments`
"""

NON_BILLABLE_MAPPING = {
    "Central Operations Central Ops and Facilities Management": 41718420,  # BE - Central Ops - Facilities
    "Central Ops Commercial & Procurement": 41718415,  # BE - Central Ops - Commercial & Procurement
    "Client Services - Delivery Client Partnerships": 42580603,  # [DT] DT - Client Partnerships & Accounts internal expenses
    "Client Services - Delivery Delivery & Product Management": 42580576,  # [DT] DT - Delivery and Product Management internal expenses
    "Client Services - Delivery Operations & Quality Assurance": 42580597,  # [DT] DT - Ops & Resourcing internal expenses
    "Client Services - Growth": 42580578,  # [DT] DT - Client Services - Growth internal expenses
    "Design": 42580512,  # [DT] DT - Design internal expenses
    "Finance": 42580589,  # [DT] DT - Finance internal expenses
    "Finance - Central Finance - Central": 41718433,  # 41718433 for BE - Finance
    "Leadership": 42591166,  # [DT] DT - Leadership internal expenses
    "Marketing & Comms": 41718437,  # BE - Marketing
    "People": 420420420,  # TPXimpact Central
    "Purpose": 41718466,  # BE - Purpose
    "Tech & Data": 42580515,  # [DT] DT - Tech & Data internal expenses
}
