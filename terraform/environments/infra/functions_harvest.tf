
# ------------------------timesheets----------------------
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "harvest_timesheet" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/harvest/timesheets"
  output_path = "${path.root}/build/harvest_timesheet.zip"
  excludes    = [".venv"]
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "harvest_timesheet" {
  source       = data.archive_file.harvest_timesheet.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.harvest_timesheet.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "harvest_timesheet" {
  name                = "harvest_timesheet_pipe"
  runtime             = var.function_runtime
  available_memory_mb = 4096
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.harvest_timesheet.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_hot.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.harvest_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.harvest_timesheets.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.harvest_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}

# --------------------------users--------------------------------\

# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "harvest_users" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/harvest/users"
  output_path = "${path.root}/build/harvest_users.zip"
  excludes    = [".venv"]
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "harvest_users" {
  source       = data.archive_file.harvest_users.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.harvest_users.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "harvest_users" {
  name                = "harvest_users_pipe"
  runtime             = var.function_runtime
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.harvest_users.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_cold.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.harvest_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.harvest_users.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.harvest_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}

# --------------------------user_project_assignments--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "harvest_user_project_assignments" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/harvest/user_project_assignments"
  output_path = "${path.root}/build/harvest_user_project_assignments.zip"
  excludes    = [".venv"]
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "harvest_user_project_assignments" {
  source       = data.archive_file.harvest_user_project_assignments.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.harvest_user_project_assignments.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "harvest_user_project_assignments" {
  name                = "harvest_user_project_assignments_pipe"
  runtime             = var.function_runtime
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.harvest_user_project_assignments.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_hot.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.harvest_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.harvest_user_project_assignments.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.harvest_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}


# --------------------------projects--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "harvest_projects" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/harvest/projects"
  output_path = "${path.root}/build/harvest_projects.zip"
  excludes    = [".venv"]
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "harvest_projects" {
  source       = data.archive_file.harvest_projects.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.harvest_projects.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "harvest_projects" {
  name                = "harvest_projects_pipe"
  runtime             = var.function_runtime
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.harvest_projects.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_cold.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.harvest_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.harvest_projects.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.harvest_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}

# --------------------------clients--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "harvest_clients" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/harvest/clients"
  output_path = "${path.root}/build/harvest_clients.zip"
  excludes    = [".venv"]
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "harvest_clients" {
  source       = data.archive_file.harvest_clients.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.harvest_clients.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "harvest_clients" {
  name                = "harvest_clients_pipe"
  runtime             = var.function_runtime
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.harvest_clients.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_cold.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.harvest_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.harvest_clients.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.harvest_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}

# --------------------------expenses--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "harvest_expenses" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/harvest/expenses"
  output_path = "${path.root}/build/harvest_expenses.zip"
  excludes    = [".venv"]
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "harvest_expenses" {
  source       = data.archive_file.harvest_expenses.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.harvest_expenses.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "harvest_expenses" {
  name                = "harvest_expenses_pipe"
  runtime             = var.function_runtime
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.harvest_expenses.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_hot.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.harvest_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.harvest_expenses.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.harvest_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}

