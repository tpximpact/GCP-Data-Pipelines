resource "google_bigquery_dataset" "harvest_raw" {
  dataset_id  = "Harvest_Raw"
  description = "Dataset for tables containing raw harvest data"
  location    = var.region

  labels = {
    env = var.env
  }
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

resource "google_bigquery_dataset" "pipedrive_raw" {
  dataset_id  = "Pipedrive_Raw"
  description = "Dataset for tables containing raw pipedrive data"
  location    = var.region

  labels = {
    env = var.env
  }
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

resource "google_bigquery_dataset" "pipedrive_processed" {
  dataset_id  = "Pipedrive_Processed"
  description = "Dataset for tables containing processed pipedrive data"
  location    = var.region

  labels = {
    env = var.env
  }
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

resource "google_bigquery_dataset" "forecast_raw" {
  dataset_id  = "Forecast_Raw"
  description = "Dataset for tables containing raw forecast data"
  location    = var.region

  labels = {
    env = var.env
  }
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}



resource "google_bigquery_dataset" "hibob_raw" {
  dataset_id  = "hibob_raw"
  description = "Dataset for hibob raw data"
  location    = var.region

  labels = {
    env = var.env
  }
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

resource "google_bigquery_dataset" "hibob_processed" {
  dataset_id  = "Hibob_Processed"
  description = "Dataset for tables containing processed hibob data"
  location    = var.region

  labels = {
    env = var.env
  }
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}


resource "google_bigquery_dataset" "helper_tables" {
  # Work out what this is for
  dataset_id  = "Helpers"
  description = "Dataset for helper tables"
  location    = var.region

  labels = {
    env = var.env
  }
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

resource "google_bigquery_dataset" "variable_data_input" {
  # Work out what this is for
  dataset_id  = "Variable_Data_Input"
  description = "Dataset for google sheets input"
  location    = var.region

  labels = {
    env = var.env
  }
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}
