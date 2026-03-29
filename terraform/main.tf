terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0" # Using the latest 2026 provider
    }
  }
}

provider "google" {
  project = var.project 
  region  = var.region  
}

# 1. The Data Lake (GCS Bucket)
resource "google_storage_bucket" "data_lake" {
  name          = var.bucket_name # Must be globally unique
  location      = var.location
  force_destroy = true
}

# 2. The Data Warehouse (BigQuery Dataset)
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.dataset_id
  location   = var.location
}