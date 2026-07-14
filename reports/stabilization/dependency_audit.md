# Dependency Audit

This report analyzes the dependency structure of the NiveshMap application, resolves the Poetry root package installation error, and classifies all declared requirements.

## 1. Poetry Root Package Error Diagnosis

### Root Cause
Streamlit Community Cloud automatically uses Poetry to resolve dependencies if a `pyproject.toml` file is present. When it runs, it attempts to install the project itself by running `poetry install`. 
Poetry expects to find a folder matching the project name (`ncr-real-estate-intelligence`) under the package root or `src/`. However:
- The source code resides in `src/ncr_intelligence/`.
- No folder matching `ncr-real-estate-intelligence` exists, causing the installer to fail with:
  `Error: No file/folder found for package ncr-real-estate-intelligence`

### Resolution
The resolution is to configure Poetry in non-package/application mode by setting `package-mode = false` in `pyproject.toml`:
```toml
[tool.poetry]
package-mode = false
```
This tells Poetry to only install the dependencies listed in `pyproject.toml` (under `[project.dependencies]`) and bypass packaging/installing the root folder itself. This is fully standard for applications/web deployments and avoids the need to rename folders or refactor import namespaces.

---

## 2. Authoritative Dependency Source
*   **Authoritative Source**: [pyproject.toml](file:///c:/Users/eklav/Desktop/NiveshMap/pyproject.toml)
*   **System Dependencies Source**: [packages.txt](file:///c:/Users/eklav/Desktop/NiveshMap/packages.txt) (contains `libgeos-dev`, `libproj-dev`, `gdal-bin`, and `libgdal-dev` required by GeoPandas and Shapely on Linux).

---

## 3. Dependency Classification

### RUNTIME_REQUIRED
These packages are directly imported and required by the Streamlit application running in `direct` mode:
*   `streamlit`: The core UI platform.
*   `pandas` & `numpy`: Essential for data operations, feasibility matrices, and model output handling.
*   `geopandas` & `shapely`: Used by the spatial database load and H3 viewport intersection logic.
*   `h3`: H3 resolution 7 cell calculations.
*   `scikit-learn`: Reconstructed models and predicting scenario foreclosure outcomes.
*   `plotly` & `matplotlib`: Dashboard chart plotting.
*   `folium` & `streamlit-folium`: Map display and viewbounds callback.
*   `pyyaml`: Parsers for configuration YAMLs (`suitability.yaml`, `localities.yaml`).
*   `pydantic` & `sqlalchemy`: Schema validations and SQLite database connection layer.
*   `requests`: Used for fallback/API calls.

### LOCAL_API_ONLY
These are only required when running the FastAPI uvicorn server locally:
*   `fastapi`
*   `uvicorn`
*   `httpx` (primarily used in FastAPI test clients)

### DEVELOPMENT_TEST
*   `pytest`: Running testing suites.
*   `jupyter`: Interactive notebooks.

### OPTIONAL_AI
*   `google-generativeai`: Optional client for Gemini AI explainer (the dashboard gracefully defaults to deterministic factors if key is not configured).

### UNUSED_OR_UNCONFIRMED
*   `psycopg2-binary`: No imports of `psycopg2` exist in either `src/` or `tests/`. (The application uses SQLite `ncr_real_estate.db`).
*   `rapidfuzz`: No imports exist.
*   `beautifulsoup4` & `lxml`: Not imported in active runtime paths, but retained for scraper test scripts in development.
