variable "project" {
  description = "Project ID"
  default     = "your-project-id"
}

variable "region" {
  description = "Region"
  default     = "us-central1"
}

variable "location" {
  description = "GCP location for resources (e.g. ASIA-SOUTHEAST1)"
  default     = "ASIA-SOUTHEAST1"
}

variable "bucket_name" {
  description = "Name of the GCS bucket to create (must be globally unique)"
  default     = "ph-economic-pulse-lake-eduardo"
}

variable "dataset_id" {
  description = "BigQuery dataset id to create/use"
  default     = "ph_economy_staging"
}
