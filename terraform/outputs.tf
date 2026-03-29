output "project" {
  description = "GCP project used for deployment"
  value       = var.project
}

output "region" {
  description = "GCP region used for deployment"
  value       = var.region
}

output "bucket_name" {
  description = "GCS bucket created for the data lake"
  value       = google_storage_bucket.data_lake.name
}

output "dataset_id" {
  description = "BigQuery dataset id created"
  value       = google_bigquery_dataset.dataset.dataset_id
}