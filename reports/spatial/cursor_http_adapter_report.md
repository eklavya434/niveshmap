# Cursor HTTP Adapter Report

## 1. Executive Verdict

**HTTP_ADAPTER_READY_WITH_BLOCKERS**

The Codex spatial service is exposed through a new FastAPI HTTP adapter at `GET /api/map/cell` and `GET /api/map/cells`. Routes are thin delegates with explicit coordinate validation, contract-aligned error codes, and 34 new endpoint tests (all passing). Cell-level price adjustment remains blocked; the adapter cannot fabricate spatial prices.

## 2. Repository State

| Item | Value |
| --- | --- |
| Branch | `main` |
| Git status before changes | Modified: `README.md`, `docs/production_setup.md`, `pyproject.toml`, `src/ncr_intelligence/database/models.py`. Untracked: Codex spatial layer files (`config/spatial.yaml`, `spatial_intelligence.py`, migration, docs, tests, reports). |
| Codex spatial files verified | Yes — all files listed in Codex report §20–21 exist and were inspected |

## 3. Existing Backend Architecture

| Component | Finding |
| --- | --- |
| Primary UI | Streamlit (`app.py`) |
| HTTP backend before this work | **None** — no FastAPI, Flask, or Django routes existed |
| Data layer | SQLAlchemy + SQLite fallback / optional PostgreSQL |
| Validation patterns | Pydantic models in `src/ncr_intelligence/utils/validation.py` |
| Spatial domain | `SpatialIntelligenceService` in `src/ncr_intelligence/geospatial/spatial_intelligence.py` |

**Decision:** Added a minimal **FastAPI** adapter (`src/ncr_intelligence/api/`) because no HTTP framework existed. Pydantic was already a project dependency; the adapter runs separately from Streamlit via `api_server.py`.

## 4. Spatial Service Verification

### `get_cell` signature

```python
def get_cell(
    self,
    latitude: float,
    longitude: float,
    quarter: Optional[str] = None,
    scenario: Optional[str] = None,
) -> dict[str, Any]
```

### `get_cells` signature

```python
def get_cells(
    self,
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    quarter: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict[str, Any]
```

### Service dependencies

- `SpatialConfig` from `config/spatial.yaml`
- Locality registry from `config/localities.yaml`
- Optional `InfrastructureAsset` and `LocalityPriceSignal` sequences (empty in default production wiring)
- In-process H3-7 cell cache; viewport filtering by centroid bounds

## 5. Routes Added

| Method | Path | Handler | Delegates to |
| --- | --- | --- | --- |
| GET | `/api/map/cell` | `get_map_cell` | `SpatialIntelligenceService.get_cell` |
| GET | `/api/map/cells` | `get_map_cells` | `SpatialIntelligenceService.get_cells` |

Entry point: `api_server.py` → `create_app()` in `src/ncr_intelligence/api/app.py`.

## 6. Request Validation

HTTP layer (`src/ncr_intelligence/api/validation.py`):

- Required parameters enforced before service call
- Non-numeric, NaN, and infinite values rejected
- Latitude/longitude range checks
- Viewport: `min_lat < max_lat`, `min_lon < max_lon` (inverted boxes not repaired)
- Invalid quarter strings map to HTTP 400 via service `ValueError`

NCR coverage check remains in the service (`UnsupportedGeographyError`).

## 7. Error Semantics

| Code | HTTP | When |
| --- | ---: | --- |
| `INVALID_COORDINATES` | 400 | Missing/invalid/inverted bounds |
| `OUTSIDE_SUPPORTED_GEOGRAPHY` | 422 | Point outside documented coverage union |
| `SPATIAL_LAYER_ERROR` | 500 | Controlled `SpatialLayerError` or unexpected internal failure |

Response shape: `{"error": {"code": "...", "message": "..."}}`. Stack traces are not exposed.

Empty viewport: HTTP 200 with `returned_cells: 0`. Service failure: HTTP 500.

## 8. Price Safety Verification

**Confirmed: no route fabricates or infers cell-level prices.**

- Routes contain no H3, price, or infrastructure calculation logic
- Routes do not import `h3`
- All price taxonomy comes from `SpatialIntelligenceService._price_response`
- Default deployment serves `SPATIAL_ESTIMATE_NOT_AVAILABLE` with `value: null`
- Numeric values appear only when the service emits `LOCALITY_LEVEL_ESTIMATE_ONLY` from an explicitly verified, non-synthetic `LocalityPriceSignal`

## 9. Tests Before Changes

| Result | Count |
| --- | ---: |
| Passed | 48 |
| Failed | 1 (`test_dashboard_dependencies` — Streamlit not installed in this environment) |
| Skipped | 0 |
| Warnings | 0 |

Codex reported 49 passed with a sandbox temp-dir error; this environment had 48 passed + 1 Streamlit import failure (environment-specific, not application logic).

## 10. Tests Added

`tests/test_map_api.py` — **34 tests**:

- 17 for `GET /api/map/cell` (validation, service delegation, taxonomy, error handling)
- 13 for `GET /api/map/cells` (validation, delegation, empty vs failure)
- 4 integration tests against real `SpatialIntelligenceService` with test fixtures

## 11. Tests After Changes

| Result | Count |
| --- | ---: |
| Passed | 82 |
| Failed | 1 (`test_dashboard_dependencies` — missing Streamlit; same environment issue) |
| Skipped | 0 |
| Warnings | 1 (Starlette/FastAPI TestClient deprecation notice) |

Spatial layer tests (17) and all prior non-dashboard tests remain green.

## 12. Files Created

- `src/ncr_intelligence/api/__init__.py`
- `src/ncr_intelligence/api/app.py`
- `src/ncr_intelligence/api/dependencies.py`
- `src/ncr_intelligence/api/errors.py`
- `src/ncr_intelligence/api/validation.py`
- `src/ncr_intelligence/api/routes/__init__.py`
- `src/ncr_intelligence/api/routes/map.py`
- `api_server.py`
- `tests/test_map_api.py`
- `docs/map_frontend_handoff.md`
- `reports/spatial/cursor_http_adapter_report.md`

## 13. Files Modified

- `pyproject.toml` — added `fastapi`, `uvicorn`; hatch wheel package path for editable installs
- `docs/map_api_contract.md` — documented HTTP status codes and adapter run instructions

## 14. API Contract Changes

Minor documentation update only:

- Added HTTP status column to error table
- Clarified HTTP 200 with null price is valid
- Added adapter run instructions and module location

No change to response JSON field taxonomy or service semantics.

## 15. Deployment Considerations

1. Run Streamlit and the map API as separate processes unless proxied behind a shared gateway.
2. Install new dependencies: `fastapi`, `uvicorn` (added to `pyproject.toml`).
3. Set `PYTHONPATH` to project root or install the package editable.
4. Production PostgreSQL + PostGIS migration remains unverified on target provider (Codex blocker).
5. Default service wiring uses YAML registries only; verified price signals and infrastructure geometry must be loaded into `SpatialIntelligenceService` before non-null prices or infrastructure metrics appear.

## 16. Remaining Blockers

- PostGIS production provider compatibility unverified
- No verified locality polygons or source-backed infrastructure geometry in repository
- No production-verified locality price-serving registry wired into default HTTP service factory
- Cell-level spatial price adjustment remains blocked (`allow_spatial_price_adjustment: false`)
- Streamlit dashboard test fails when `streamlit` is not installed (environment dependency, not adapter defect)

## 17. Exact Antigravity Handoff

Build the visible map UI against the running HTTP adapter:

1. **Start API:** `python api_server.py` (port 8000).
2. **Viewport:** On pan/zoom, call `GET /api/map/cells?min_lat=…&min_lon=…&max_lat=…&max_lon=…`. Render each `cells[].cell.geometry` GeoJSON polygon.
3. **Click:** On map click, call `GET /api/map/cell?lat=…&lon=…`. Highlight returned polygon; populate side panel from response fields verbatim.
4. **Styling:**
   - `SPATIAL_ESTIMATE_NOT_AVAILABLE` / `INFRASTRUCTURE_INTELLIGENCE_ONLY` / `UNSUPPORTED` → distinct non-numeric styles; **no heatmap colour**
   - `LOCALITY_LEVEL_ESTIMATE_ONLY` → show value with mandatory locality-level disclaimer
5. **Errors:** HTTP 422 outside coverage → user message, no nearest-cell snap. HTTP 500 → error banner, not empty success.
6. **Do not** compute H3, distances, readiness, or prices client-side. See `docs/map_frontend_handoff.md`.
