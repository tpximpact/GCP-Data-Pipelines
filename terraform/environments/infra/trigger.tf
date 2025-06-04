resource "google_pubsub_topic" "cloud_function_trigger_cold" {
  name         = "cloud-function-trigger-cold"
  kms_key_name = google_kms_crypto_key.pub_sub_key.id
}

resource "google_cloud_scheduler_job" "daily-4-45" {
  name        = "daily-4-45-trigger"
  description = "Scheduled daily to trigger cloud function at 04:45 and 12:45"
  schedule    = "45 4,12 * * *"

  pubsub_target {
    # topic.id is the topic's full resource name.
    topic_name = google_pubsub_topic.cloud_function_trigger_cold.id
    data       = base64encode("daily")
  }
}

resource "google_pubsub_topic" "cloud_function_trigger_hot" {
  name         = "cloud-function-trigger-hot"
  kms_key_name = google_kms_crypto_key.pub_sub_key.id
}

resource "google_cloud_scheduler_job" "hourly-00" {
  name        = "every-hour-00"
  description = "Scheduled to trigger cloud function every hour from 6 through 18"
  schedule    = "0 6-18 * * *"

  pubsub_target {
    # topic.id is the topic's full resource name.
    topic_name = google_pubsub_topic.cloud_function_trigger_hot.id
    data       = base64encode("01hr00min")
  }
}

resource "google_pubsub_topic" "cloud_function_trigger_hot_2" {
  name         = "cloud-function-trigger-hot-2"
  kms_key_name = google_kms_crypto_key.pub_sub_key.id
}

resource "google_cloud_scheduler_job" "hourly-15" {
  name        = "every-hour-15"
  description = "Scheduled to trigger cloud function 15 past every hour from 6 through 18"
  schedule    = "15 6-18 * * *"

  pubsub_target {
    # topic.id is the topic's full resource name.
    topic_name = google_pubsub_topic.cloud_function_trigger_hot_2.id
    data       = base64encode("01hr15min")
  }
}
