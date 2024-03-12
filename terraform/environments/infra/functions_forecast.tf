# --------------------------assignments--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "forecast_assignments" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/forecast/assignments"
  output_path = "/tmp/forecast_assignments.zip"
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "forecast_assignments" {
  source       = data.archive_file.forecast_assignments.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.forecast_assignments.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "forecast_assignments" {
  name                = "forecast_assignments_pipe"
  runtime             = "python39" # of course changeable
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.forecast_assignments.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point                  = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_hot.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.forecast_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.forecast_assignments.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.forecast_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project

  }
}


# --------------------------assignments_filled--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "forecast_assignments_filled" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/forecast/assignments_filled"
  output_path = "/tmp/forecast_assignments_filled.zip"
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "forecast_assignments_filled" {
  source       = data.archive_file.forecast_assignments_filled.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.forecast_assignments_filled.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "forecast_assignments_filled" {
  name                = "forecast_assignments_filled_pipe"
  runtime             = "python310" # of course changeable
  available_memory_mb = 1024
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.forecast_assignments_filled.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point                  = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_hot_2.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.forecast_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.forecast_assignments_filled.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.forecast_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project

  }
}

# --------------------------people--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "forecast_people" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/forecast/people"
  output_path = "/tmp/forecast_people.zip"
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "forecast_people" {
  source       = data.archive_file.forecast_people.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.forecast_people.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "forecast_people" {
  name                = "forecast_people_pipe"
  runtime             = "python39" # of course changeable
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.forecast_people.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point                  = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_cold.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.forecast_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.forecast_people.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.forecast_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project

  }
}

# --------------------------projects--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "forecast_projects" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/forecast/projects"
  output_path = "/tmp/forecast_projects.zip"
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "forecast_projects" {
  source       = data.archive_file.forecast_projects.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.forecast_projects.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "forecast_projects" {
  name                = "forecast_projects_pipe"
  runtime             = "python39" # of course changeable
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.forecast_projects.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point                  = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_hot.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.forecast_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.forecast_projects.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.forecast_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project

  }
}


# --------------------------placeholders--------------------------------\
# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "forecast_placeholders" {
  type        = "zip"
  source_dir  = "../../../cloud_functions/forecast/placeholders"
  output_path = "/tmp/forecast_placeholders.zip"
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "forecast_placeholders" {
  source       = data.archive_file.forecast_placeholders.output_path
  content_type = "application/zip"

  # Append to the MD5 checksum of the files's content
  # to force the zip to be updated as soon as a change occurs
  name   = "cloud_function-${data.archive_file.forecast_placeholders.output_md5}.zip"
  bucket = data.google_storage_bucket.function_bucket.name
}

resource "google_cloudfunctions_function" "forecast_placeholders" {
  name                = "forecast_placeholders_pipe"
  runtime             = "python39" # of course changeable
  available_memory_mb = 512
  timeout             = 540
  # Get the source code of the cloud function as a Zip compression
  source_archive_bucket = data.google_storage_bucket.function_bucket.name
  source_archive_object = google_storage_bucket_object.forecast_placeholders.name

  # Must match the function name in the cloud function `main.py` source code
  entry_point                  = "main"
  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = google_pubsub_topic.cloud_function_trigger_hot.id
  }

  environment_variables = {
    "DATASET_ID"           = google_bigquery_dataset.forecast_raw.dataset_id
    "TABLE_NAME"           = google_bigquery_table.forecast_placeholders.table_id
    "TABLE_LOCATION"       = google_bigquery_dataset.forecast_raw.location
    "GOOGLE_CLOUD_PROJECT" = var.project

  }
}
