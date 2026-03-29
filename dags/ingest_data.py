"""
Airflow DAG for ingesting both food price and poverty datasets into GCS and BigQuery.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.models import Variable
from datetime import datetime
import logging
from pathlib import Path
import pandas as pd
import requests
import io

# Project Constants
# The DAG reads a few configuration values from Airflow Variables so deployments
# can be customized through the Airflow UI or the CLI. Set these variables in
# Admin -> Variables or via the `airflow variables` CLI inside your Airflow
# container. See README for exact commands.
# - ph_bq_project: BigQuery project id (e.g. my-gcp-project)
# - ph_bq_dataset: BigQuery dataset id (e.g. ph_economy_staging)
# - ph_bucket_name: GCS bucket name to write raw data to
BUCKET_NAME = Variable.get("ph_bucket_name", default_var="ph-economic-pulse-lake-eduardo")
WFP_URL = Variable.get("ph_wfp_url", default_var="https://data.humdata.org/dataset/ea251823-8694-47b4-82d0-7d27f00e8aba/resource/9a842d72-0d7d-4922-ad0e-eb8106c1ab0e/download/wfp_food_prices_phl.csv")
POVERTY_URL = Variable.get("ph_poverty_url", default_var="https://data.humdata.org/dataset/c2840912-2adb-494b-8dc7-983166802b98/resource/10c50bf6-8310-47f3-bcdd-e33cc6bc7791/download/poverty_phl.csv")
ECONOMIC_GROWTH_URL = Variable.get("ph_economic_url", default_var="https://data.humdata.org/dataset/ea251823-8694-47b4-82d0-7d27f00e8aba/resource/9a842d72-0d7d-4922-ad0e-eb8106c1ab0e/download/economy_growth_phl.csv")

# BigQuery destination configuration (project and dataset can be set in Airflow)
BQ_PROJECT = Variable.get("ph_bq_project", default_var="your-gcp-project-id")
BQ_DATASET = Variable.get("ph_bq_dataset", default_var="ph_economy_staging")

# Fallback path to bundled CSV in repo when remote source is unavailable
LOCAL_ECONOMY_GROWTH_CSV = Path(__file__).resolve().parents[1] / "data" / "economy-and-growth_phl.csv"

def download_food_price_data():
    response = requests.get(WFP_URL)
    response.raise_for_status()
    if response.text.strip().startswith("<html") or "<!DOCTYPE html>" in response.text:
        raise ValueError("CRITICAL ERROR: The URL returned HTML instead of a CSV. Check the direct download link.")
    df = pd.read_csv(io.StringIO(response.text), skiprows=[1])
    df.columns = [c.lower().replace(' ', '_').replace('/', '_') for c in df.columns]
    required_cols = [
        "date", "admin1", "market", "category", "commodity", "unit",
        "priceflag", "pricetype", "currency", "price", "usdprice"
    ]
    df = df[required_cols]
    df.to_csv("/tmp/food_prices_raw.csv", index=False)

def download_poverty_data():
    response = requests.get(POVERTY_URL)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text), skiprows=[1])
    df.columns = [c.lower().replace(' ', '_').replace('.', '') for c in df.columns]
    df.to_csv("/tmp/poverty_raw.csv", index=False)
    print(f"Success! Ingested {len(df)} years of poverty metrics.")
    
def download_economic_growth_data():
    output_path = Path("/tmp/economy_growth.csv")

    try:
        response = requests.get(ECONOMIC_GROWTH_URL, timeout=30)
        response.raise_for_status()
        if response.text.strip().startswith("<html") or "<!DOCTYPE html>" in response.text:
            raise ValueError("CRITICAL ERROR: The URL returned HTML instead of CSV content.")

        df = pd.read_csv(io.StringIO(response.text), skiprows=[1])
        df.columns = [c.lower().replace(' ', '_').replace('.', '') for c in df.columns]
        logging.info("Economy growth CSV downloaded from remote source with %d rows", len(df))

    except Exception as ex:
        logging.warning("Remote economy growth fetch failed (%s); using local fallback seed: %s", ex, LOCAL_ECONOMY_GROWTH_CSV)
        if not LOCAL_ECONOMY_GROWTH_CSV.exists():
            raise RuntimeError(f"Fallback economy growth CSV not found at {LOCAL_ECONOMY_GROWTH_CSV}")

        df = pd.read_csv(LOCAL_ECONOMY_GROWTH_CSV)
        df.columns = [c.lower().replace(' ', '_').replace('.', '') for c in df.columns]

    df.to_csv(output_path, index=False)
    print(f"Success! Economy growth data ready at {output_path} with {len(df)} rows.")

with DAG(
    dag_id="ph_economic_pulse_data_ingestion",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False
) as dag:

    download_food_prices_task = PythonOperator(
        task_id="download_food_prices_csv",
        python_callable=download_food_price_data
    )

    upload_food_prices_to_gcs_task = LocalFilesystemToGCSOperator(
        task_id="upload_food_prices_to_gcs",
        src="/tmp/food_prices_raw.csv",
        dst="raw/wfp_food_prices.csv",
        bucket=BUCKET_NAME,
        gcp_conn_id="google_cloud_default"
    )

    load_food_prices_to_bq_task = GCSToBigQueryOperator(
        task_id="load_food_prices_to_bq",
        bucket=BUCKET_NAME,
        source_objects=["raw/wfp_food_prices.csv"],
        destination_project_dataset_table=f"{BQ_PROJECT}.{BQ_DATASET}.wfp_prices_raw",
        schema_fields=[
            {"name": "date", "type": "DATE", "mode": "NULLABLE"},
            {"name": "admin1", "type": "STRING", "mode": "NULLABLE"},
            {"name": "market", "type": "STRING", "mode": "NULLABLE"},
            {"name": "category", "type": "STRING", "mode": "NULLABLE"},
            {"name": "commodity", "type": "STRING", "mode": "NULLABLE"},
            {"name": "unit", "type": "STRING", "mode": "NULLABLE"},
            {"name": "priceflag", "type": "STRING", "mode": "NULLABLE"},
            {"name": "pricetype", "type": "STRING", "mode": "NULLABLE"},
            {"name": "currency", "type": "STRING", "mode": "NULLABLE"},
            {"name": "price", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "usdprice", "type": "FLOAT", "mode": "NULLABLE"},
        ],
        write_disposition="WRITE_TRUNCATE",
        skip_leading_rows=1,
        source_format="CSV",
        time_partitioning={"type": "MONTH", "field": "date"},
        cluster_fields=["commodity", "market"],
        gcp_conn_id="google_cloud_default"
    )

    download_poverty_task = PythonOperator(
        task_id="download_poverty_csv",
        python_callable=download_poverty_data
    )

    upload_poverty_to_gcs_task = LocalFilesystemToGCSOperator(
        task_id="upload_poverty_to_gcs",
        src="/tmp/poverty_raw.csv",
        dst="raw/poverty_phl.csv",
        bucket=BUCKET_NAME,
        gcp_conn_id="google_cloud_default"
    )

    load_poverty_to_bq_task = GCSToBigQueryOperator(
        task_id="load_poverty_to_bq",
        bucket=BUCKET_NAME,
        source_objects=["raw/poverty_phl.csv"],
        destination_project_dataset_table=f"{BQ_PROJECT}.{BQ_DATASET}.poverty_phl_raw",
        schema_fields=[
            {"name": "country_name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "country_iso3", "type": "STRING", "mode": "NULLABLE"},
            {"name": "year", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "indicator_name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "indicator_code", "type": "STRING", "mode": "NULLABLE"},
            {"name": "value", "type": "FLOAT", "mode": "NULLABLE"},
        ],
        write_disposition="WRITE_TRUNCATE",
        skip_leading_rows=1,
        source_format="CSV",
        gcp_conn_id="google_cloud_default"
    )
    

    download_economy_task = PythonOperator(
        task_id="download_economy_csv",
        python_callable=download_economic_growth_data
    )

    upload_economy_to_gcs_task = LocalFilesystemToGCSOperator(
        task_id="upload_economy_to_gcs",
        src="/tmp/economy_growth.csv",
        dst="raw/economy_growth.csv",
        bucket=BUCKET_NAME,
        gcp_conn_id="google_cloud_default"
    )

    load_economy_to_bq_task = GCSToBigQueryOperator(
        task_id="load_economy_to_bq",
        bucket=BUCKET_NAME,
        source_objects=["raw/economy_growth.csv"],
        destination_project_dataset_table=f"{BQ_PROJECT}.{BQ_DATASET}.economy_growth_raw",
        autodetect=True, # Let BigQuery guess the schema first
        write_disposition="WRITE_TRUNCATE", # Overwrite every time we run
        source_format="CSV",
        skip_leading_rows=1,
        gcp_conn_id="google_cloud_default"
    )

    # Set task dependencies for all 3 datasets
    download_food_prices_task >> upload_food_prices_to_gcs_task >> load_food_prices_to_bq_task
    download_poverty_task >> upload_poverty_to_gcs_task >> load_poverty_to_bq_task
    download_economy_task >> upload_economy_to_gcs_task >> load_economy_to_bq_task