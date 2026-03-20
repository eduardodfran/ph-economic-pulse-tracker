## Plan: PhilsPulse 32-Point Capstone

Deliver a batch-first, reproducible, Windows-friendly modern data stack project that maps every rubric criterion to concrete evidence artifacts. The recommended path is to lock an MVP that guarantees full rubric coverage first (problem framing, cloud+IaC, orchestrated ingestion, optimized BigQuery models, dbt transformations, 2-tile dashboard, reproducibility), then add optional quality extras (tests/CI) only after the core path is working.

**Steps**

1. Phase 0: Scope lock and scoring matrix. Freeze v1 scope as daily batch at 06:00 PHT, mandatory 3-source ingestion (WFP food prices, PH real-time prices, PH poverty stats), local-first peer-review workflow with optional cloud demo, and optional extras deferred. Create a rubric-to-evidence checklist in the README/docs so each criterion has an explicit proof artifact. **Status: Completed (2026-03-15). Evidence: README.md and docs/rubric-evidence-matrix.md**
2. Phase 1: Repository and environment foundation. Define a clean project structure with separate areas for infrastructure, orchestration, transformations, dashboard, docs, and scripts. Add environment templates and ignore rules for secrets/state files. _Blocks phases 2-5._
3. Phase 1: Cloud provisioning via Terraform. Provision GCS raw landing bucket, BigQuery datasets (staging + marts), and service account/IAM with least privilege. Include variableized configuration and reproducible apply flow for reviewers. _Depends on step 2._
4. Phase 2: Batch ingestion DAG in Airflow (Docker). Build one orchestrated DAG scheduled daily 06:00 PHT with parallel source fetch tasks, schema/quality validation task, and load tasks into BigQuery staging. Add retries, idempotent loads, and logging. _Depends on step 3._
5. Phase 2: Data contracts and landing conventions. Standardize raw schema fields (date, region/province, commodity/category, price/value, source metadata) and enforce source-specific staging table naming conventions for downstream dbt. _Parallel with step 4 after interfaces are defined._
6. Phase 3: dbt transformation layers. Implement staging models (type casting, normalization, dedupe), intermediate harmonization models, and marts/fact models that compute the core metric (international vs local price gap) and region-sensitive inflation indicators. Add schema.yml docs and tests for not_null/unique/relationships/accepted_values. _Depends on steps 4-5._
7. Phase 3: BigQuery performance optimization. Materialize dashboard-facing marts as partitioned tables by date/month and clustered by province/commodity (and optionally source) with rationale documented against expected query filters. Verify optimization via table metadata output and benchmark query scans before/after. _Depends on step 6._
8. Phase 4: Streamlit dashboard delivery. Build at least 2 required tiles: one temporal trend tile (rice vs fuel over time) and one categorical/regional tile (inflation heatmap or grouped regional distribution), with filters for date range, commodity, and region. Keep local-first run path mandatory; optional deployed demo link can be added afterward. _Depends on steps 6-7._
9. Phase 5: Reproducibility and grading evidence hardening. Produce a reviewer-friendly README + setup guide that can be executed end-to-end on Windows + Docker with minimal manual steps. Add architecture diagram, rubric evidence map, screenshots, and troubleshooting for credentials/path issues. _Depends on steps 2-8._
10. Phase 6: Optional excellence track (non-blocking). After core rubric completion, add CI for Terraform validation + dbt tests + Airflow DAG parse checks, plus lightweight unit/integration tests for ingestion logic. _Depends on step 9 and is explicitly out of core scoring path._

**Relevant files**

- `c:/Users/Wakin/Main/Projects/ph-economic-pulse-tracker/.agents/data-engineer.md` — seed the planning/governance document for agent-guided execution and task boundaries.
- `c:/Users/Wakin/Main/Projects/ph-economic-pulse-tracker/README.md` — primary rubric-to-evidence map and runbook entrypoint (to be created).
- `c:/Users/Wakin/Main/Projects/ph-economic-pulse-tracker/docker-compose.yml` — local orchestration runtime for reproducibility (to be created).
- `c:/Users/Wakin/Main/Projects/ph-economic-pulse-tracker/terraform/` — IaC definitions for GCS/BigQuery/IAM (to be created).
- `c:/Users/Wakin/Main/Projects/ph-economic-pulse-tracker/airflow/dags/` — orchestrated batch ingestion DAGs and task graph (to be created).
- `c:/Users/Wakin/Main/Projects/ph-economic-pulse-tracker/dbt/` — transformations, tests, docs, and model lineage (to be created).
- `c:/Users/Wakin/Main/Projects/ph-economic-pulse-tracker/streamlit/` — dashboard app implementation (to be created).
- `c:/Users/Wakin/Main/Projects/ph-economic-pulse-tracker/docs/` — architecture, setup, optimization rationale, screenshots, troubleshooting (to be created).

**Verification**

1. Rubric traceability review: each criterion has at least one explicit artifact and one execution proof listed in README/docs.
2. Infrastructure reproducibility: Terraform init/plan/apply succeeds on clean environment; resources match expected naming and regions.
3. Orchestration validity: Airflow DAG parses and runs on schedule in Docker; all source tasks complete with retries tested.
4. Data quality gate: staging row counts and schema checks pass; dbt test suite passes for documented constraints.
5. Performance gate: dashboard queries hit partition+clustered marts and show lower bytes processed than non-optimized baseline.
6. Product gate: Streamlit shows required 2+ tiles with correct filters and data freshness annotation.
7. Reviewer simulation: clone + env setup + docker-compose up + first DAG run + dashboard access can be completed using docs without ad-hoc fixes.

**Decisions**

- Included scope: Batch pipeline only (not streaming), daily schedule at 06:00 PHT, all 3 datasets in MVP, local-first reproducibility mandatory.
- Excluded from core path: CI/CD, advanced testing, and cloud-hosted production deployment (optional after rubric-complete baseline).
- Architecture preference: minimize operational complexity while still using cloud-native components required by rubric.

**Further Considerations**

1. Poverty statistics cadence mismatch: decide between last-known-value carry-forward vs monthly refresh join strategy before final mart logic; recommended default is monthly snapshot join with explicit null handling notes.
2. Region key harmonization: align province/region taxonomies across datasets early to avoid late-stage dashboard inconsistencies; recommended to maintain a small conformed dimension table.
3. Cost controls: enforce partition filters in dashboard SQL and limit historical scan defaults to reduce BigQuery query costs during demos.

## Phase 0 Deliverables

- Scope decisions are locked for v1.
- Rubric-to-evidence matrix is created at docs/rubric-evidence-matrix.md.
- README now includes phase status and links to the scoring matrix.
