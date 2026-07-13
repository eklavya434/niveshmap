# Production Deployment & Automation Guide

This guide explains how to transition this platform from the offline development/sandbox configuration to a production-grade automated deployment.

## 1. Relational Database Migration (SQLite to PostgreSQL)

During local development, the platform connects to a local SQLite database file at `data/ncr_real_estate.db`. In production, set the following environment variables in your `.env` configuration:

```bash
DB_HOST=your-production-db-instance-uri
DB_PORT=5432
DB_NAME=ncr_intelligence
DB_USER=ncr_admin
DB_PASSWORD=your-secure-password
```

The DB connection pool in `src/ncr_intelligence/database/connection.py` automatically detects these host variables, establishes a connection pool to your PostgreSQL instance, and configures declarative SQLAlchemy schemas.

To initialize database schemas in PostgreSQL, run:
```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/schema.sql
```

---

## 2. Ingestion Pipeline Orchestration (Apache Airflow / Cron)

Since RERA listings and circle rate registries are protected behind anti-bot CAPTCHAs, official downloads of raw snapshots are conducted manually. 

Once snapshots are placed in the raw ingestion bucket (e.g. `data/sample/` locally or an AWS S3/Google Cloud Storage prefix in production), the collection orchestrator (`scripts/collect_phase0.py`) should be triggered.

### Cron Automation Example
To run the ingestion pipeline every Sunday at 00:00:
```bash
0 0 * * 0 cd /path/to/NiveshMap && .venv/bin/python scripts/collect_phase0.py >> logs/ingestion.log 2>&1
```

### Apache Airflow DAG Structure Recommendation
For enterprise scaling, model the ingestion pipeline as an Airflow DAG with the following task sequences:
1. `Verify_New_Raw_Snapshots_Sensor` (verifies presence of weekly/quarterly circles or RERA tables).
2. `Execute_Ingestion_Orchestrator` (runs `collect_phase0.py` to parse, validate via Pydantic, and load into PostgreSQL).
3. `Calculate_Geospatial_Overlays` (triggers `build_phase0_dataset.py` to recalculate distances and rebuild the analytical panel).
4. `Check_Data_Quality_Gates` (verifies that readiness scores meet the hard gates).

---

## 3. Machine Learning Model Retraining Schedule

The ML model (`data/processed/forecaster.pickle`) should be retrained quarterly whenever the National Housing Bank (NHB) publishes its new HPI Residex baseline.

To schedule model retraining:
```bash
0 0 1 */3 * cd /path/to/NiveshMap && .venv/bin/python scripts/train_forecaster.py >> logs/model_training.log 2>&1
```
The script will run temporal cross-validation, print/log the validation MAE/RMSE/MAPE errors, and overwrite the model binary.

---

## 4. Grounded AI Explanation Setup

To configure the live investment scenario summary report writer:
1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/).
2. Add the key to your local environment shell or `.env` file:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```
3. Restart the Streamlit application. The dashboard's explainability tab will automatically transition to online status and generate reports dynamically.
