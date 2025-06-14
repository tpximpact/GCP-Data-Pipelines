# --------------------------time_off--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "hibob_time_off" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/hibob/time_off"
  output_path = "${path.root}/build/hibob_time_off.zip"
  excludes    = [".venv"]
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "hibob_time_off" {
  source       = data.archive_file.hibob_time_off.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.hibob_time_off.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "hibob_time_off" {
  name                = "hibob_time_off_pipe"
  runtime             = var.function_runtime
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.hibob_time_off.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_hot.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.hibob_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.time_off.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.hibob_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}


# --------------------------employees--------------------------------\
data "archive_file" "hibob_employees" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/hibob/employees"
  output_path = "${path.root}/build/hibob_employees.zip"
  excludes    = [".venv"]
}

resource "google_storage_bucket_object" "hibob_employees" {
  source       = data.archive_file.hibob_employees.output_path
  content_type = "application/zip"
  name         = "cloud_function-${data.archive_file.hibob_employees.output_md5}.zip"
  bucket       = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "hibob_employees" {
  name                  = "hibob_employees_pipe"
  runtime               = var.function_runtime
  available_memory_mb   = 512
  timeout               = 540
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.hibob_employees.name

  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_cold.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.hibob_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.employees.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.hibob_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}

# --------------------------time_off_policies--------------------------------\
data "archive_file" "hibob_time_off_policies" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/hibob/time_off_policies"
  output_path = "${path.root}/build/hibob_time_off_policies.zip"
  excludes    = [".venv"]
}

resource "google_storage_bucket_object" "hibob_time_off_policies" {
  source       = data.archive_file.hibob_time_off_policies.output_path
  content_type = "application/zip"
  name         = "cloud_function-${data.archive_file.hibob_time_off_policies.output_md5}.zip"
  bucket       = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "hibob_time_off_policies" {
  name                  = "hibob_time_off_policies_pipe"
  runtime               = var.function_runtime
  available_memory_mb   = 256
  timeout               = 540
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.hibob_time_off_policies.name

  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_cold.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.hibob_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.time_off_policies.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.hibob_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}

# --------------------------holiday_balances--------------------------------\
data "archive_file" "hibob_holiday_balances" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/hibob/holiday_balances"
  output_path = "${path.root}/build/hibob_holiday_balances.zip"
  excludes    = [".venv"]
}

resource "google_storage_bucket_object" "hibob_holiday_balances" {
  source       = data.archive_file.hibob_holiday_balances.output_path
  content_type = "application/zip"
  name         = "cloud_function-${data.archive_file.hibob_holiday_balances.output_md5}.zip"
  bucket       = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "hibob_holiday_balances" {
  name                  = "hibob_holiday_balances_pipe"
  runtime               = var.function_runtime
  available_memory_mb   = 512
  timeout               = 540
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.hibob_holiday_balances.name

  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_cold.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.hibob_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.holiday_balances.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.hibob_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project
  }
}
