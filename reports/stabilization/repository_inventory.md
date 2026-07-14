# Repository Inventory

This report catalogs the files and structure of the NiveshMap repository on the `stabilization` branch.

## Key Components

### 1. Application Entry Points
*   **Streamlit Frontend**: [app.py](file:///c:/Users/eklav/Desktop/NiveshMap/app.py) - Main interactive platform containing the map, questionnaire, suitability matching, and Plotly visualization.
*   **FastAPI Backend**: [api_server.py](file:///c:/Users/eklav/Desktop/NiveshMap/api_server.py) - Uvicorn server entry point for running the map API backend locally.

### 2. Source Code
*   **API Layer**: Located under [src/ncr_intelligence/api](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/api/)
    *   [app.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/api/app.py) - FastAPI application definition.
    *   [dependencies.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/api/dependencies.py) - Database connections and service builders.
    *   [validation.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/api/validation.py) - Geospatial coordinate and bounds parser.
    *   [errors.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/api/errors.py) - HTTP error response payloads.
    *   [routes/map.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/api/routes/map.py) - FastAPI GET `/cell` and `/cells` endpoints.
*   **Geospatial Layer**: Located under [src/ncr_intelligence/geospatial](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/geospatial/)
    *   [spatial_intelligence.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/geospatial/spatial_intelligence.py) - H3 cell caching and query engine.
    *   [spatial_client.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/geospatial/spatial_client.py) - Switchable Client abstraction (`SpatialClient`, `HTTPSpatialClient`, `DirectSpatialClient`).
    *   [distances.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/geospatial/distances.py) & [geocoding.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/geospatial/geocoding.py) - Geospatial helper services.
*   **Modeling & Suitability Layer**: Located under [src/ncr_intelligence/modeling](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/modeling/)
    *   [forecaster.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/modeling/forecaster.py) - Scenario-conditioned price forecaster.
    *   [models.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/modeling/models.py) - Baseline models.
    *   [suitability.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/modeling/suitability.py) - Profile validation, financial capacity calculation, and suitability engines.
    *   [llm_explainer.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/modeling/llm_explainer.py) - Gemini explainer with deterministic fallback.

### 3. Configuration & Data
*   **Configurations**:
    *   [config/suitability.yaml](file:///c:/Users/eklav/Desktop/NiveshMap/config/suitability.yaml) - Centralized financial capacity and scoring weights.
    *   [config/spatial.yaml](file:///c:/Users/eklav/Desktop/NiveshMap/config/spatial.yaml) - Regional spatial parameters.
    *   [config/localities.yaml](file:///c:/Users/eklav/Desktop/NiveshMap/config/localities.yaml) - Localities metadata.
*   **SQLite Databases**:
    *   [data/ncr_real_estate.db](file:///c:/Users/eklav/Desktop/NiveshMap/data/ncr_real_estate.db) - Sqlite database containing H3 spatial layers and transaction data.
*   **Processed Data**:
    *   [data/processed/forecaster.pickle](file:///c:/Users/eklav/Desktop/NiveshMap/data/processed/forecaster.pickle) - Serialized forecasting engine.
    *   [data/processed/phase0_quarterly_panel.csv](file:///c:/Users/eklav/Desktop/NiveshMap/data/processed/phase0_quarterly_panel.csv) - Processed baseline panel dataset.
    *   [data/processed/locality_feasibility.csv](file:///c:/Users/eklav/Desktop/NiveshMap/data/processed/locality_feasibility.csv) - Regional feasibility indicators.

### 4. Verification & Testing
*   **Tests Suite**: 99 unit tests under [tests/](file:///c:/Users/eklav/Desktop/NiveshMap/tests/).
*   **Scripts**: Data extraction and training scripts under [scripts/](file:///c:/Users/eklav/Desktop/NiveshMap/scripts/).

### 5. Deployment & Configuration
*   **Streamlit Community Cloud Configs**: [packages.txt](file:///c:/Users/eklav/Desktop/NiveshMap/packages.txt) (system C libraries) and [pyproject.toml](file:///c:/Users/eklav/Desktop/NiveshMap/pyproject.toml) (with `[tool.poetry] package-mode = false`).
*   **Hugging Face Spaces Configs**: [Dockerfile](file:///c:/Users/eklav/Desktop/NiveshMap/Dockerfile), [.dockerignore](file:///c:/Users/eklav/Desktop/NiveshMap/.dockerignore), [scripts/start.sh](file:///c:/Users/eklav/Desktop/NiveshMap/scripts/start.sh), and [.github/workflows/deploy-huggingface.yml](file:///c:/Users/eklav/Desktop/NiveshMap/.github/workflows/deploy-huggingface.yml) (push trigger disabled).
