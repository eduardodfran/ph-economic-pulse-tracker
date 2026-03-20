# Rubric to Evidence Matrix

This document is the Phase 0 scoring checklist for peer review.

## Scope Lock Snapshot

- Date locked: 2026-03-15
- Pipeline mode: batch
- DAG schedule: 06:00 PHT daily
- Mandatory datasets:
  - WFP food prices
  - Philippines real-time prices
  - Philippines poverty statistics
- Delivery mode: local-first, optional cloud demo

## Rubric Coverage Checklist

| Criterion                      | Required for 4 points                                             | Planned evidence artifact                                       | Execution proof                            |
| ------------------------------ | ----------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------ |
| Problem description            | Clear problem, stakeholders, and expected insight outcome         | docs/problem-statement.md                                       | README summary and peer-readable narrative |
| Cloud + IaC                    | Cloud resources provisioned through IaC                           | terraform/main.tf, terraform/variables.tf, terraform/outputs.tf | terraform plan and apply logs              |
| Data ingestion + orchestration | End-to-end DAG with multiple tasks loading to data lake/warehouse | airflow/dags/ingest_pipeline.py                                 | Airflow run logs and task graph screenshot |
| Data warehouse optimization    | Partitioning and clustering aligned with query patterns           | dbt/models/marts/\*.sql and optimization notes                  | BigQuery table metadata screenshot         |
| Transformations                | dbt staging and marts with tests/docs                             | dbt/dbt_project.yml, dbt/models, dbt/tests, dbt/schema.yml      | dbt run and dbt test output                |
| Dashboard                      | At least 2 tiles: temporal + categorical                          | streamlit/app.py                                                | Dashboard screenshot with both tiles       |
| Reproducibility                | Clear setup instructions and runnable commands                    | README.md and docs/setup.md                                     | Fresh clone run-through checklist          |

## Phase 0 Done Criteria

- [x] Scope decisions are frozen.
- [x] Rubric criteria are mapped to explicit artifacts.
- [x] Proof expectations are defined per criterion.
- [ ] Artifact paths exist in repository.
- [ ] Proof outputs are collected during implementation phases.

## Review Notes

This matrix is updated as implementation progresses so each rubric item has both code evidence and runtime proof before submission.
