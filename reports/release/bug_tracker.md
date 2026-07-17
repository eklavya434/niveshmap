# Release Candidate Bug Tracker

This tracker catalogues all resolved blockers, high, and medium-severity bugs identified and fixed throughout the stabilization lifecycle of NiveshMap.

## Bug Classification & Resolution Log

| Bug ID | Severity | Component | Description | Affected Files | Fix Applied |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-01** | **BLOCKER** | `llm_explainer.py` | `NameError: name 'List' is not defined` during type evaluation at startup. | [llm_explainer.py](file:///c:/Users/eklav/Desktop/NiveshMap/src/ncr_intelligence/modeling/llm_explainer.py) | Added explicit `List` import from `typing`. |
| **BUG-02** | **BLOCKER** | `pyproject.toml` | Poetry build failed to locate packages during Streamlit Community Cloud deployment. | [pyproject.toml](file:///c:/Users/eklav/Desktop/NiveshMap/pyproject.toml) | Configured `package-mode = false` in Poetry section. |
| **BUG-03** | **BLOCKER** | `data/processed/` | App failed to boot on fresh Git clones due to git-ignored model pickle and CSVs. | `data/processed/` | Force-committed baseline model pickle and CSV panel datasets. |
| **BUG-04** | **HIGH** | `packages.txt` | App crashed on Linux due to missing geospatial C libraries (`libgeos`, `libgdal`, etc.). | `packages.txt` | Created `packages.txt` containing required apt-get dependencies. |
| **BUG-05** | **MEDIUM** | `app.py` | UI crashed with `IndexError` if selected locality had missing database observations. | [app.py](file:///c:/Users/eklav/Desktop/NiveshMap/app.py) | Added empty DataFrame guards (`.empty`) with graceful `st.error()` message and `st.stop()`. |

---

## Bug Regression Tests
- **BUG-01**: Verified via clean-import scripts. Tested that importing `StrategySuitabilityExplainer` succeeds.
- **BUG-02 / BUG-03 / BUG-04**: Verified via clean container execution on Streamlit Community Cloud.
- **BUG-05**: Verified by mocking an empty locality query in unit tests, ensuring no unhandled array bounds exception is thrown.
