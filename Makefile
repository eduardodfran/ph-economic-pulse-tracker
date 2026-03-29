.PHONY: infra terraform-validate up stop dbt-seed dbt-run dbt-build dashboard airflow

# Run terraform init/plan/apply (requires gcloud auth and TF_VARs set)
infra:
	cd terraform && terraform init && terraform plan -out=tfplan && terraform apply -auto-approve tfplan

terraform-validate:
	cd terraform && terraform init && terraform fmt -check && terraform validate

# Start services via Docker Compose
up:
	docker compose up -d

stop:
	docker compose down

# dbt commands: ensure your dbt profile exists (see ph_pulse_dbt/profiles.yml.template)
dbt-seed:
	cd ph_pulse_dbt && dbt seed --profiles-dir $(DBT_PROFILES_DIR)

dbt-run:
	cd ph_pulse_dbt && dbt build --profiles-dir $(DBT_PROFILES_DIR) --vars "use_seed: true"

dbt-build:
	cd ph_pulse_dbt && dbt build --profiles-dir $(DBT_PROFILES_DIR)

dashboard:
	streamlit run app.py

airflow:
	docker compose up -d
