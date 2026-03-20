# Project Charter: PhilsPulse

## Project Name

PhilsPulse: National Economic Ingestion and Analytics Pipeline

## Problem Statement

Philippine market volatility often lacks transparent, localized data correlation. PhilsPulse builds a production-grade data platform to ingest, warehouse, and visualize long-horizon commodity price trends by bridging global food benchmarks with local real-time market indicators and poverty context.

## Primary Objective

Deliver a full-score capstone project by demonstrating end-to-end capability in cloud infrastructure, orchestration, and analytics engineering.

## Core Questions the Dashboard Answers

- How do local food and energy prices move over time versus global benchmarks?
- Which regions show elevated poverty vulnerability under rising staple prices?
- Where do international and local market prices diverge most significantly?

## In-Scope Data Sources

### 1) WFP Global Food Prices Database

- Role in project: Global benchmark for commodity pricing
- Coverage notes: Historical depth beginning as early as 1992 for some countries, broader coverage from later years
- Project use: Benchmark comparison against local market behavior

### 2) Philippines Real Time Prices (World Bank RTP)

- Role in project: Weekly local market signal for food, energy, and exchange dynamics
- Coverage notes: Weekly updates with model-based gap filling
- Project use: Local trend layer for near-current movement

### 3) Philippines Poverty Statistics (PSA-derived with PSGC)

- Role in project: Socioeconomic context by geography
- Coverage notes: Official poverty incidence and magnitude metrics with geographic keys
- Project use: Vulnerability lens for regional interpretation

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
