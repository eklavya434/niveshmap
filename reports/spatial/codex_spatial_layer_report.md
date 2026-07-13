# Codex Spatial Layer Report

## 1. Executive Verdict

**SPATIAL_INTELLIGENCE_READY_PRICE_ADJUSTMENT_BLOCKED**

The repository can now resolve a documented NCR coverage-zone click to a deterministic H3 cell, preserve locality assignment provenance, return a map-ready response, and enforce temporal infrastructure feature rules. It cannot defensibly produce cell-varying prices from its current data.

## 2. Existing Repository Architecture

The project is a Python 3.11+ Streamlit application (`app.py`) with SQLAlchemy models, local SQLite fallback (`data/ncr_real_estate.db`), a raw PostgreSQL DDL reference (`sql/schema.sql`), YAML configuration, and pytest. The current UI is Streamlit, not Next.js. No HTTP backend, FastAPI/Flask routes, map library, vector tile service, or authentication layer exists.

The existing scenario engine is `ScenarioForecaster`. It is locality-trained and uses the locality × quarter panel with stage and centroid-derived feature inputs. The existing readiness scorer is separate locality Data Readiness. No current frontend map exists.

## 3. Existing Geospatial Capabilities

Before this work the repository had Haversine utilities, GeoPandas/Shapely point handling, locality centroids, and mock project coordinate lists in Phase-0 scripts. It had no H3 index, locality polygons, persisted geometry, time-versioned geometry source, viewport logic, or map click contract.

The mock coordinate lists remain excluded from the new spatial layer. They are not recast as verified map data.

## 4. Database and PostGIS Status

Local development uses SQLite whenever PostgreSQL environment variables are absent. PostgreSQL is optionally configured through `.env.example`; no provider/deployment configuration is present. PostGIS was therefore not enabled or verified before this change.

`sql/migrations/001_spatial_price_intelligence.sql` now performs `CREATE EXTENSION IF NOT EXISTS postgis`, defines SRID-4326 geometries, and adds GiST/B-tree indexes. Production readiness remains conditional on the target provider supporting PostGIS and the deploy role having extension privilege. SQLite stores WKT plus explicit SRID columns for local tests only.

## 5. H3 Resolution Evaluation

| Resolution | Average area | Current coverage cells | Finding |
| --- | ---: | ---: | --- |
| 6 | 36.129 km² | 11 | Too coarse for useful infrastructure-distance variation. |
| 7 | 5.161 km² | 76 | Selected zone-level resolution. |
| 8 | 0.737 km² | 508 | Too fine for locality-centroid price context; high false-precision risk. |

Counts use the documented 3 km locality-centroid coverage union. Details and re-grid strategy: [spatial_resolution.md](../../docs/spatial_resolution.md).

## 6. Selected Spatial Resolution

H3 resolution **7** is configured once in `config/spatial.yaml`. It is a zone-level infrastructure lens, not a parcel grid. The configuration also owns feature version, geometry gating, and viewport limit.

## 7. Supported NCR Geometry Strategy

No NCR or locality boundary dataset exists in the repository. The implemented strategy is a union of 3 km buffers around the 16 Phase-0 locality registry centroids, measured in EPSG:32643 and stored with source provenance. This covers candidate analytical areas only; it must not be portrayed as a complete NCR administrative map or exact locality boundary.

## 8. Cell-Locality Assignment Method

Reliable locality polygons are unavailable, so `NEAREST_CENTROID_FALLBACK` is used within a 4 km assignment gate. Every response preserves `assignment_method`, `assignment_distance_km`, and `assignment_quality_class`. A cell can remain `UNASSIGNED`; no nearest-locality fiction is returned outside supported coverage.

## 9. Infrastructure Geometry Audit

The existing data model has project/event metadata and project-locality links but no source-backed station, corridor, or airport geometries. The new `infrastructure_geometries` schema records geometry role, quality, availability date, source, and SRID. The feature pipeline requires station points for metro, route lines for expressways/highways, and documented airport point/boundary geometry. Project centroids are rejected for corridor distance.

### Spatial feature feasibility matrix

| Feature group | Required source and geometry | As-of-quarter requirement | Current availability | Feasibility | Leakage risk |
| --- | --- | --- | --- | --- | --- |
| Operational/proposed metro distance and counts | Source-backed station `Point` plus stage events | Station geometry and public stage evidence must be available by quarter | No verified geometry | Pipeline ready; source load blocked | High, protected by event/publication + geometry date gates |
| RRTS distance/count | Station points or documented corridor line plus events | Same temporal rule | No verified geometry | Pipeline ready; source load blocked | High, protected |
| Expressway/highway distance | Route `LineString` / `MultiLineString` plus events | Route and operational stage must be available by quarter | No verified route geometry | Pipeline ready; point-centroid proxy rejected | High, protected |
| Airport distance | Documented point or boundary plus stage events | Geometry/site evidence must be available by quarter | No verified reference geometry | Pipeline ready; source load blocked | Medium, protected |
| Active/proposed/construction/operational project counts | Any valid time-versioned spatial asset | Asset and stage must be public by quarter | No verified spatial assets | Pipeline ready; source load blocked | High, protected |

## 10. Temporal Spatial Feature Methodology

The layer reuses the existing `get_project_stage_at_quarter` rule: both the physical event date and public article/document date must be no later than the requested quarter. It also requires the geometry availability date to be as-of that quarter. Future stations and unpublished proposals cannot leak into historic features.

## 11. Price Signal Audit

The project correctly distinguishes transaction, listing, circle rate, RERA, index, and proxy fields in schema/validation. However, its generated Phase-0 panel explicitly creates mock price trends for feasibility and its database/sample inputs are not registered as production spatial-serving signals. There is no parcel transaction/value source and no cell target labels.

The new `LocalityPriceSignal` gate requires `verified_for_spatial_serving=True`, a non-null value, and `is_synthetic=False`. Without that explicit provenance status the response carries no value.

## 12. Spatial Adjustment Feasibility

No defensible spatial adjustment is available. Transparent regression, residual, hierarchical, and gradient-boosting approaches are blocked by missing cell labels, verified geometry, and non-synthetic serving data. The selected method is no cell adjustment. Full analysis: [spatial_adjustment_feasibility.md](spatial_adjustment_feasibility.md).

## 13. Selected Price Output Taxonomy

The service recognizes `PARCEL_VERIFIED`, `CELL_MODEL_ESTIMATE`, `LOCALITY_ANCHORED_CELL_ESTIMATE`, `LOCALITY_LEVEL_ESTIMATE_ONLY`, `PRICE_SIGNAL_ONLY`, and `SPATIAL_ESTIMATE_NOT_AVAILABLE`. Current code emits only `LOCALITY_LEVEL_ESTIMATE_ONLY` for an approved locality signal, or `SPATIAL_ESTIMATE_NOT_AVAILABLE`. It never calls a locality value a cell prediction.

## 14. Cell Spatial Readiness Methodology

Spatial readiness is categorical rather than a fabricated weighted score:

- `LOCALITY_ANCHORED_ONLY` requires a defensible locality assignment and verified non-synthetic price signal.
- `INFRASTRUCTURE_INTELLIGENCE_ONLY` requires usable time-valid geometry but not a price signal.
- `UNSUPPORTED` applies when neither gate is met or assignment is absent.
- `FULL_SPATIAL_ESTIMATE` is reserved for a future validated cell adjustment.

It reports assignment quality, coordinate completeness, locality price readiness, infrastructure geometry quality, temporal completeness, and spatial-adjustment support separately.

## 15. API Endpoints Added

The current Streamlit architecture has no server route layer. The backend now implements the map API contract as transport-neutral service operations:

- `SpatialIntelligenceService.get_cell` → `GET /api/map/cell`
- `SpatialIntelligenceService.get_cells` → `GET /api/map/cells`

They validate coordinates, reject unsupported geography, resolve H3 cells, apply temporal features, return taxonomy/readiness/limitations, and limit viewport payloads. An HTTP adapter should mount these methods without reimplementing logic. See [map_api_contract.md](../../docs/map_api_contract.md).

## 16. Scenario Engine Integration

The existing forecaster accepts locality context. The spatial service returns `scenario_scope: LOCALITY_MODEL_WITH_SPATIAL_CONTEXT` and `NOT_EVALUATED`; it does not assert that the locality-trained model is cell-trained. The visual/client integration can use the returned locality ID and spatial feature version to pass context to the current scenario flow.

## 17. Performance Assessment

Resolution 7 creates 76 cells for current coverage, so GeoJSON viewport responses are small. The contract filters by viewport centroid and applies a 500-cell cap. PostgreSQL has planned GiST geometry filtering plus locality/region and cell-quarter B-tree indexes. No Redis, Kafka, vector tiles, or microservice were added. At a future wider NCR boundary or resolution increase, measure payload size and query plans before selecting vector tiles.

## 18. Tests Before Changes

Baseline `pytest` collected 32 tests: **31 passed, 1 errored**. The lone error occurred before the test body because pytest could not access its default user temporary directory in the sandbox. It was not an analytical assertion failure.

## 19. Tests After Changes

Run after changes with a workspace-writable base temporary directory and cache disabled: **49 passed in 3.02 seconds**. This is the original 32 plus 17 spatial-layer tests. The spatial tests cover H3 determinism, invalid/out-of-coverage coordinates, valid/SRID geometry, assignment provenance, temporal leakage, corridor semantics, unavailable geometry, price hard gates, synthetic blocking, viewport filtering, duplicate H3 rejection, and scenario scope.

## 20. Files Created

- `config/spatial.yaml`
- `src/ncr_intelligence/geospatial/spatial_intelligence.py`
- `scripts/build_spatial_layer.py`
- `sql/migrations/001_spatial_price_intelligence.sql`
- `tests/test_spatial_intelligence.py`
- `docs/spatial_architecture.md`
- `docs/spatial_resolution.md`
- `docs/spatial_distance_semantics.md`
- `docs/map_api_contract.md`
- `reports/spatial/spatial_adjustment_feasibility.md`

## 21. Files Modified

- `pyproject.toml` — official H3 dependency.
- `src/ncr_intelligence/database/models.py` — portable spatial ORM models.
- `README.md` — Spatial Intelligence operating and limitation guidance.
- `docs/production_setup.md` — PostGIS deployment requirement.

## 22. Deployment Requirements

1. Install `h3` from the pinned project dependency range.
2. Provision PostgreSQL with PostGIS and a migration role allowed to create the extension.
3. Apply base schema then `sql/migrations/001_spatial_price_intelligence.sql`.
4. Run the baseline locality pipeline and `scripts/build_spatial_layer.py` in deployment.
5. Load source-backed infrastructure geometries with provenance and availability dates.
6. Register only approved non-synthetic locality price signals for spatial serving.
7. Add an HTTP adapter only if the map is deployed separately from Streamlit.

## 23. Remaining Blockers

- No target-provider PostGIS compatibility verification.
- No verified locality or administrative polygons.
- No source-backed infrastructure route/station/airport geometry in the repository.
- No non-synthetic production locality price-serving registry or cell-level labels.
- No validated spatial price-adjustment study or uncertainty model.
- No current HTTP route layer or visual map component.

## 24. Exact Instructions for Antigravity

Build a minimal visual map integration without changing the spatial analytics:

1. Mount a thin HTTP adapter around `SpatialIntelligenceService.get_cell` and `get_cells`, preserving the JSON and error codes in `docs/map_api_contract.md`; do not calculate H3, distances, readiness, or price types in the UI.
2. Request viewport cells on move/zoom and call the click operation for a selected point. Render the returned GeoJSON polygon as the selected analytical zone.
3. Use a distinct non-numeric visual state for `SPATIAL_ESTIMATE_NOT_AVAILABLE`, `INFRASTRUCTURE_INTELLIGENCE_ONLY`, and `UNSUPPORTED`. Never colour these as a price heatmap.
4. In the click panel, display estimate type, price-signal type, assignment method/distance, spatial readiness, all available infrastructure metrics, feature status, and limitations verbatim.
5. Label every numeric locality output “Locality-level price signal — not a parcel or cell valuation.” Do not display a numeric price for blocked cells.
6. If a scenario is selected, show `LOCALITY_MODEL_WITH_SPATIAL_CONTEXT` and retain the existing locality scenario chart; do not describe it as a cell forecast.
