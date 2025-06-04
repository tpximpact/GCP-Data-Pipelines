resource "google_bigquery_table" "trainline_results" {
  dataset_id = google_bigquery_dataset.trainline.dataset_id
  table_id   = "results"

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
