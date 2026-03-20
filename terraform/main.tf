terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0" # Using the latest 2026 provider
    }
  }
}

provider "google" {
  project = "zoomcamp-data-engineer-484608" # Replace with your actual Project ID
  region  = "asia-southeast1"    # Singapore is closest to Manila
}

# 1. The Data Lake (GCS Bucket)
resource "google_storage_bucket" "data_lake" {
  name          = "ph-economic-pulse-lake-eduardo" # Must be globally unique
  location      = "ASIA-SOUTHEAST1"
  force_destroy = true
}

# 2. The Data Warehouse (BigQuery Dataset)
resource "google_bigquery_dataset" "dataset" {
  dataset_id = "ph_economy_staging"
  location   = "ASIA-SOUTHEAST1"
}