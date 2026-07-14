# Stabilization Bug Log

This log compiles the issues identified and corrected during the end-to-end NiveshMap stabilization audit.

## Bug Table

| ID | Component | Severity | Reproduction | Root Cause | Fix Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | `llm_explainer.py` | **BLOCKER** | Import `StrategySuitabilityExplainer` from `src.ncr_intelligence.modeling.llm_explainer`. | `List` was used in type annotations but not imported from `typing`. | **FIXED** (added import). |
| **BUG-02** | `pyproject.toml` | **BLOCKER** | Run Poetry installer on Streamlit Community Cloud. | Poetry tried to install the root project but could not resolve the package name folder. | **FIXED** (set `package-mode = false`). |
| **BUG-03** | `.gitignore` / `data/` | **BLOCKER** | Launch Streamlit app on a clean Git checkout. | Processed ML model pickle and dataset CSVs were ignored by Git, leaving them absent in deployment. | **FIXED** (force-committed assets). |
| **BUG-04** | `packages.txt` | **HIGH** | Run GeoPandas/Shapely operations on Streamlit Cloud Linux environment. | Required system-level C libraries (`libgeos-dev`, `libproj-dev`, etc.) were not installed in the container. | **FIXED** (created `packages.txt`). |

---

## Low Severity Warnings (Documented)
*   **Starlette Test Client Warning**: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
    *   *Status*: Ignored. This is a deprecation warning from external package FastAPI/Starlette test harness and does not affect runtime application stability.
