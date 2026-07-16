# Quality Assurance Bug Report

This bug tracker catalogs all runtime, integration, and logic issues identified and fixed during the Quality Assurance review of NiveshMap.

## Bug Table

| ID | Severity | Component | Description | Affected Files | Fix Applied |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | **BLOCKER** | `llm_explainer.py` | `NameError: name 'List' is not defined` during python import check. | [llm_explainer.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/modeling/llm_explainer.py) | Imported `List` from `typing` package. |
| **BUG-02** | **BLOCKER** | `pyproject.toml` | Build failed with "No file/folder found for package ncr-real-estate-intelligence" on Streamlit Cloud. | [pyproject.toml](file:///c:/Users/eklav/Desktop/NiveshMap/pyproject.toml) | Configured `package-mode = false` in `[tool.poetry]`. |
| **BUG-03** | **BLOCKER** | `data/processed` | App UI blocked with warning: "Baseline datasets or serialized ML models are missing." | `data/processed/` | Force-committed baseline datasets and model pickle to Git. |
| **BUG-04** | **HIGH** | `packages.txt` | App failed to boot on Linux due to missing GDAL/GEOS C-extensions. | `packages.txt` | Declared Linux packages `libgeos-dev`, `libproj-dev`, `gdal-bin`, and `libgdal-dev` for container install. |
| **BUG-05** | **MEDIUM** | `app.py` | App crashes with `IndexError` if selected locality has missing history or feasibility data. | [app.py](file:///c:/Users/eklav/Desktop/NiveshMap/app.py) | Added empty DataFrame guards to check if `loc_history` or `feasibility_df` are empty, halting gracefully. |

---

## Detailed Bug Diagnostics

### BUG-05: Missing Dataframe Empty Guards in app.py
*   **Steps to reproduce**:
    1. Define a new locality entry in `config/localities.yaml` (e.g. `TEST_LOCALITY`).
    2. Start the Streamlit app and select `TEST_LOCALITY` from the sidebar dropdown.
    3. The app crashes immediately with `IndexError: single positional indexer is out-of-bounds` because the new locality has no entries in `phase0_quarterly_panel.csv` or `locality_feasibility.csv`.
*   **Root Cause**: The data queries did not check if the sliced DataFrames `loc_history` and `feasibility_df` were empty before calling `.iloc[-1]` or `.iloc[0]`.
*   **Fix Applied**: Added `.empty` guards to display a clean warning via `st.error()` and halt UI execution using `st.stop()` rather than raising an unhandled exception.
