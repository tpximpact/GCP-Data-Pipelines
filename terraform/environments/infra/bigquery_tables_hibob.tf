resource "google_bigquery_table" "time_off" {
  dataset_id = google_bigquery_dataset.hibob_raw.dataset_id
  table_id   = "time_off"

  time_partitioning {
    type = "DAY"
  }

  labels = {
    env = var.env
  }

  deletion_protection = false

  encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

resource "google_bigquery_table" "employees" {
  dataset_id = google_bigquery_dataset.hibob_raw.dataset_id
  table_id   = "employees"

  time_partitioning {
    type = "DAY"
  }

  labels = {
    env = var.env
  }

  deletion_protection = false

  encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

resource "google_bigquery_table" "time_off_policies" {
  dataset_id = google_bigquery_dataset.hibob_raw.dataset_id
  table_id   = "time_off_policies"

  time_partitioning {
    type = "DAY"
  }

  labels = {
    env = var.env
  }

  deletion_protection = false

  encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

resource "google_bigquery_table" "holiday_balances" {
  dataset_id = google_bigquery_dataset.hibob_raw.dataset_id
  table_id   = "holiday_balances"

  time_partitioning {
    type = "DAY"
  }

  labels = {
    env = var.env
  }

  deletion_protection = false

  encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery_key.id
  }
}

