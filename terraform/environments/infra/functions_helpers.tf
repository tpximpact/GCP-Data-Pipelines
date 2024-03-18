# --------------------------months_columns--------------------------------
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "helpers_months_columns" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/helpers/months_columns"
  output_path = "/tmp/helpers_months_columns.zip"
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "helpers_months_columns" {
  source       = data.archive_file.helpers_months_columns.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.helpers_months_columns.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "helpers_months_columns" {
  name                = "helpers_months_columns_pipe"
  runtime             = var.function_runtime
  available_memory_mb = 1024
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.helpers_months_columns.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_cold.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.helper_tables.dataset_id
    "TABLE_NAME"           = google_bigquery_table.months_columns.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.helper_tables.location
    "GOOGLE_CLOUD_PROJECT" = var.project

  }
}
