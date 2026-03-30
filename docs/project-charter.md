# Project Charter: PhilsPulse

## Project Name

PhilsPulse: National Economic Ingestion and Analytics Pipeline

## Problem Statement

Philippine market volatility often lacks transparent, localized data correlation. PhilsPulse builds a production-grade data platform to ingest, warehouse, and visualize long-horizon commodity price trends by bridging food price, macroeconomic growth, and poverty indicators.

## Primary Objective

Deliver a full-score capstone project by demonstrating end-to-end capability in cloud infrastructure, orchestration, and analytics engineering.

## Core Questions the Dashboard Answers

- How do local food and energy prices move over time versus global benchmarks?
- Which regions show elevated poverty vulnerability under rising staple prices?
- Where do international and local market prices diverge most significantly?

## In-Scope Data Sources

### 1) WFP Food Prices for Philippines (HDX)

- Source page: https://data.humdata.org/dataset/wfp-food-prices-for-philippines
- Role in project: Food price movement signal for market-level trend analysis
- Coverage notes: Historical market observations by commodity and location
- Project use: Price trend analysis and downstream regional/categorical dashboard tiles

### 2) World Bank Economy and Growth Indicators for Philippines (HDX)

- Source page: https://data.humdata.org/dataset/world-bank-economy-and-growth-indicators-for-philippines
- Role in project: Macroeconomic context for growth and economic performance
- Coverage notes: Country-level indicator series across years
- Project use: Economic context layer for interpreting food price and poverty shifts

### 3) World Bank Poverty Indicators for Philippines (HDX)

- Source page: https://data.humdata.org/dataset/world-bank-poverty-indicators-for-philippines
- Role in project: Socioeconomic vulnerability context
- Coverage notes: Poverty-related indicator series by year
- Project use: Vulnerability lens for regional and temporal interpretation

## Analytical Scope for MVP

- Pipeline mode: Batch only
- Refresh cadence: Daily DAG run at 06:00 PHT
- Required outputs:
  - Temporal tile: Historical trend of selected commodities (for example rice and fuel)
  - Categorical or regional tile: Regional inflation or vulnerability distribution
- Derived metric: Price gap between international benchmark and local prices

## Tooling Decisions for MVP

- Cloud: GCP
- Data lake: Google Cloud Storage
- Warehouse: BigQuery
- IaC: Terraform
- Orchestration: Airflow in Docker
- Transformations: dbt
- Programming: Python
- Visualization: Streamlit

## Explicitly Optional for MVP

- Jupyter notebooks for exploration only
- PySpark unless scale exceeds BigQuery plus dbt needs
- Bruin unless course requires it
- Kafka or Redpanda unless architecture is changed to streaming

## Success Criteria

- Full rubric evidence exists for each scoring criterion.
- A reviewer can run the project locally from a clean clone using documented steps.
- Dashboard presents at least two required tiles using transformed warehouse tables.

## Risks and Mitigations

- Cadence mismatch across datasets: Use documented join logic by period and explicit null handling.
- Geographic key mismatch: Build a conformed location mapping table early.
- Query cost growth: Enforce partition filters and clustering-aligned access patterns.

## Submission Evidence Targets

- Infrastructure: Terraform apply logs and resource definitions
- Orchestration: DAG graph and successful run logs
- Transformations: dbt run and dbt test outputs plus model docs
- Warehouse optimization: BigQuery partition and cluster metadata
- Dashboard: Screenshots of required tiles
- Reproducibility: Setup guide validated by peer-style run-through



