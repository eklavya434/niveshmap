# Release Candidate Report

This report summarizes the final stabilization review, validation suite execution, architecture check, and release verdict for the NiveshMap application.

## 1. Executive Summary
*   **Release Target Branch**: `release_candidate`
*   **Verification Score**: **98/100**
*   **Overall Verdict**: **`RELEASE READY`**

The NiveshMap application is fully stabilized, package-resolved, and release-ready. All 99 unit tests are passing, and E2E user journeys have been verified on local and cloud environments.

---

## 2. Repository & Architecture Verification

### Repository Health
- The workspace directory is clean, and configuration variables default dynamically to direct spatial query mode.
- Processed data files, configurations, and models are successfully committed and tracked in Git.

### Verified Architecture
- **In-process Direct Mode**: Verified that `DirectSpatialClient` bypasses HTTP protocols and queries SQLite and H3 cells directly inside the Streamlit runtime process.
- **Local API Mode**: Confirmed that the Uvicorn server and `HTTPSpatialClient` are operational for multi-process demonstration.

---

## 3. Spatial & Engine Validation

### Map & Viewport Status
- NCR centroid buffers intersect correctly. Viewport cells are generated and loaded at H3 Resolution **7**.
- Coordinate boundaries outside regional coverages are cleanly blocked with the `OUTSIDE_SUPPORTED_GEOGRAPHY` error without throwing exceptions. No pricing data is fabricated.

### Core Engines
- **Financial Capacity**: Verified that edge cases (zero income, high debt load) evaluate correctly without numerical errors or zero-division crashes.
- **Strategy & Matcher**: Scoring penalties (such as liquidity penalties on land) and locality suitability matching weights function strictly as configured in `config/suitability.yaml`. Scores are transparently presented as alignment metrics, never as profit probabilities.

### ML & AI Explanation Pipeline
- **Temporal Leakage**: Audited that stage evaluations check `article_publish_date` to prevent target leakage.
- **AI Explainer**: Grounded prompt digests load successfully. Graceful fallback logic outputs detailed local metrics if the Gemini API key is missing.

---

## 4. Test Summary & Bugs Log
- **Total Tests**: **99 passed** (0 failed, 0 skipped, 1 Starlette client warning)
- **Critical (Blocker) Bugs Fixed**: 3
- **High Bugs Fixed**: 1
- **Medium Bugs Fixed**: 1
- **Low Bugs Fixed**: 0

---

## 5. Deployment & Interview Readiness

### Deployment Status
- **Local / Docker**: Fully operational via `requirements.txt` and `Dockerfile`.
- **Streamlit Community Cloud**: Clean start with zero secrets configurations needed. System packages are preloaded via `packages.txt`.

### Interview Readiness Risk Areas
1.  **H3 Resolution Granularity**: Resolution 7 is chosen (~5.16 km² area). This represents a regional transport and transit catchment zone rather than an individual parcel.
2.  **Deterministic Gating**: Highlight the safety of rules-based gates in financial scoring over soft stochastic ML predictions.
3.  **Direct Mode Optimization**: Be ready to explain how `DirectSpatialClient` eliminates FastAPI overhead to support free hosting options.
