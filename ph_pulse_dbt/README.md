# ph_pulse_dbt

This folder contains dbt models for transforming raw/staging tables into analytics-ready marts for the PhilsPulse dashboard.

## Official Dataset Sources (HDX)

1. [WFP Food Prices for Philippines](https://data.humdata.org/dataset/wfp-food-prices-for-philippines)
2. [World Bank Economy and Growth Indicators for Philippines](https://data.humdata.org/dataset/world-bank-economy-and-growth-indicators-for-philippines)
3. [World Bank Poverty Indicators for Philippines](https://data.humdata.org/dataset/world-bank-poverty-indicators-for-philippines)

## Partitioning and Performance

I implemented partitioning by year on the `fct_food_prices` table (partitioned by the `report_month` column) to optimize query costs in BigQuery, following best practices for large-scale analytical warehouses. This ensures efficient scans and lower costs for time-based queries.

## Architecture Diagram

```mermaid
flowchart LR
    WFP[WFP Food Prices (PH)] --> Airflow[Airflow DAG]
    ECON[WB Economy and Growth (PH)] --> Airflow
    POV[WB Poverty Indicators (PH)] --> Airflow
    Airflow --> GCS[Google Cloud Storage]
    GCS --> BQ[BigQuery]
    BQ --> dbt[dbt]
    dbt --> Streamlit[Streamlit Dashboard]
```

## Batch Ingestion Logic

Although the data is historical, the pipeline is designed as a batch ingestion system. Airflow orchestrates daily runs that load CSV snapshots into BigQuery staging tables. dbt transforms and documents those tables into analytics-ready models for dashboard use.

## How to Run (Reproducibility)

This dbt project is configured to run against BigQuery. For local reproducibility we include a `profiles.yml` template and a short checklist.

1. Install dbt and project dependencies (see top-level `requirements.txt`):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
pip install dbt-bigquery==1.11.1
```

2. Create your dbt profile

Copy the provided template into your dbt profiles location (default `~/.dbt`):

```bash
mkdir -p ~/.dbt
cp profiles.yml.template ~/.dbt/profiles.yml
# Edit ~/.dbt/profiles.yml to confirm values, or rely on the env vars listed in .env.example
```

The template uses environment variables: set `GCP_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS`, and optionally `DBT_DATASET` or `GCP_REGION`.

3. Optional: use local seeds for offline work

```bash
cd ph_pulse_dbt
dbt seed --profiles-dir $(DBT_PROFILES_DIR)
dbt build --profiles-dir $(DBT_PROFILES_DIR) --vars "use_seed: true"
```

![PLACEHOLDER - dbt seed/build output screenshot goes here](../docs/screenshots/dbt-seed-build-output.png)

4. Production run (against your live BigQuery dataset)

```bash
cd ph_pulse_dbt
dbt build --profiles-dir $(DBT_PROFILES_DIR)
```

![PLACEHOLDER - production dbt build output screenshot goes here](../docs/screenshots/dbt-production-build-output.png)

If you prefer not to copy `profiles.yml` to `~/.dbt`, set the `DBT_PROFILES_DIR` environment variable to point to this folder and dbt will use that profiles file.

## Evidence Placeholders

- PLACEHOLDER: Add screenshot path for `dbt run` success output.
- PLACEHOLDER: Add screenshot path for `dbt test` success output.
- PLACEHOLDER: Add screenshot path for dbt lineage/docs page (if generated).

Insert dbt docs lineage screenshot here (if you run `dbt docs generate` and `dbt docs serve`):

![PLACEHOLDER - dbt docs lineage screenshot goes here](../docs/screenshots/dbt-docs-lineage.png)
