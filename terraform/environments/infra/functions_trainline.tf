# # --------------------------trainline--------------------------------
# # Generates an archive of the source code compressed as a .zip file.
# data "archive_file" "trainline" {
#   type        = "zip"
#   source_dir  = "../../../cloud_functions/trainline"
#   output_path = "${path.root}/build/trainline.zip"
# }

# # Add source code zip to the Cloud Function's bucket
# resource "google_storage_bucket_object" "trainline" {
#   source       = data.archive_file.trainline.output_path
#   content_type = "application/zip"

#   # Append to the MD5 checksum of the files's content
#   # to force the zip to be updated as soon as a change occurs
#   name   = "cloud_function-${data.archive_file.trainline.output_md5}.zip"
#   bucket = data.google_storage_bucket.function_bucket.name
# }

# resource "google_cloudfunctions_function" "trainline" {
#   name                = "trainline_harvest_upload"
#   runtime             = var.function_runtime
#   available_memory_mb = 512
#   timeout             = 540
#   # Get the source code of the cloud function as a Zip compression
#   source_archive_bucket = data.google_storage_bucket.function_bucket.name
#   source_archive_object = google_storage_bucket_object.trainline.name

#   # Must match the function name in the cloud function `main.py` source code
#   entry_point = "main"
#   event_trigger {
#     event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
#     resource   = google_pubsub_topic.cloud_function_trigger_cold.id
#   }

#   environment_variables = {
#     "DATASET_ID"           = google_bigquery_dataset.trainline.dataset_id
#     "TABLE_NAME"           = google_bigquery_table.trainline_results.table_id
#     "TABLE_LOCATION"       = google_bigquery_dataset.trainline.location
#     "GOOGLE_CLOUD_PROJECT" = var.project
#   }
# }
