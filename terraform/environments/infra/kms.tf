data "google_kms_key_ring" "dashboards_keyring" {
  name     = "dashboards_keyring"
  location = var.region
}

resource "google_kms_crypto_key" "pub_sub_key" {
  name     = "pubsub_key"
  key_ring = data.google_kms_key_ring.dashboards_keyring.id
}

resource "google_kms_crypto_key" "bigquery_key" {
  name     = "bigquery_key"
  key_ring = data.google_kms_key_ring.dashboards_keyring.id
}
# data "google_iam_policy" "bigquery_key_encrypt_decrypt" {
#   binding {
#     role = "roles/cloudkms.cryptoKeyVersions.useToEncrypt"
#     members = [
#       "serviceAccount:bq-${data.google_project.project_number.number}@bigquery-encryption.iam.gserviceaccount.com",
#     ]
#   }
# }
resource "google_kms_crypto_key_iam_member" "bigquery_key_encrypt_decrypt" {
  crypto_key_id = google_kms_crypto_key.bigquery_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:bq-${data.google_project.project_number.number}@bigquery-encryption.iam.gserviceaccount.com"

}
resource "google_kms_crypto_key_iam_member" "pubsub_key_encrypt_decrypt" {
  crypto_key_id = google_kms_crypto_key.pub_sub_key.id

  role   = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member = "serviceAccount:service-${data.google_project.project_number.number}@gcp-sa-pubsub.iam.gserviceaccount.com"

}
