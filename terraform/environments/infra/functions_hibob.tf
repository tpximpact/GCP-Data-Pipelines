# --------------------------time_off--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "hibob_time_off" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/hibob/time_off"
  output_path = "/tmp/hibob_time_off.zip"
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
  runtime             = "python39" # of course changeable
  available_memory_mb = 1024
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.hibob_time_off.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point                  = "main"
  https_trigger_security_level = "SECURE_ALWAYS"
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
