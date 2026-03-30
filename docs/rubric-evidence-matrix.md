# Rubric to Evidence Matrix

This document is the Phase 0 scoring checklist for peer review.

## Scope Lock Snapshot

- Date locked: 2026-03-15
- Pipeline mode: batch
- DAG schedule: 06:00 PHT daily
- Mandatory datasets:
  - WFP Food Prices for Philippines (HDX)
  - World Bank Economy and Growth Indicators for Philippines (HDX)
  - World Bank Poverty Indicators for Philippines (HDX)
- Delivery mode: local-first, optional cloud demo

Dataset source pages:

- https://data.humdata.org/dataset/wfp-food-prices-for-philippines
- https://data.humdata.org/dataset/world-bank-economy-and-growth-indicators-for-philippines
- https://data.humdata.org/dataset/world-bank-poverty-indicators-for-philippines

## Rubric Coverage Checklist

| Criterion                      | Required for 4 points                                             | Planned evidence artifact                                             | Execution proof                            |
| ------------------------------ | ----------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------ |
| Problem description            | Clear problem, stakeholders, and expected insight outcome         | docs/project-charter.md                                               | README summary and peer-readable narrative |
| Cloud + IaC                    | Cloud resources provisioned through IaC                           | terraform/main.tf, terraform/variables.tf, terraform/outputs.tf       | terraform plan and apply logs              |
| Data ingestion + orchestration | End-to-end DAG with multiple tasks loading to data lake/warehouse | dags/ingest_data.py                                                   | Airflow run logs and task graph screenshot |
| Data warehouse optimization    | Partitioning and clustering aligned with query patterns           | ph_pulse_dbt/models/marts/\*.sql and optimization notes               | BigQuery table metadata screenshot         |
| Transformations                | dbt staging and marts with tests/docs                             | ph_pulse_dbt/dbt_project.yml, ph_pulse_dbt/models, ph_pulse_dbt/tests | dbt run and dbt test output                |
| Dashboard                      | At least 2 tiles: temporal + categorical                          | app.py                                                                | Dashboard screenshot with both tiles       |
| Reproducibility                | Clear setup instructions and runnable commands                    | README.md and docs/project-charter.md                                 | Fresh clone run-through checklist          |

## Phase 0 Done Criteria

- [x] Scope decisions are frozen.
- [x] Rubric criteria are mapped to explicit artifacts.
- [x] Proof expectations are defined per criterion.
- [ ] Artifact paths exist in repository.
- [ ] Proof outputs are collected during implementation phases.

## Review Notes

This matrix is updated as implementation progresses so each rubric item has both code evidence and runtime proof before submission.

## Evidence Placeholders

- PLACEHOLDER: Airflow DAG graph screenshot path
- PLACEHOLDER: Airflow successful run log screenshot path
- PLACEHOLDER: Terraform apply output file or screenshot path
- PLACEHOLDER: dbt run/dbt test output screenshot path
- PLACEHOLDER: BigQuery partition/cluster metadata screenshot path
- PLACEHOLDER: Dashboard screenshot paths for 2 required tiles

Suggested screenshot placement paths:

- docs/screenshots/terraform-apply-proof.png
- docs/screenshots/airflow-dag-graph.png
- docs/screenshots/airflow-successful-run-logs.png
- docs/screenshots/dbt-build-output.png
- docs/screenshots/dbt-docs-lineage.png
- docs/screenshots/bigquery-partition-cluster-metadata.png
- docs/screenshots/dashboard-tile-temporal.png
- docs/screenshots/dashboard-tile-categorical.png
