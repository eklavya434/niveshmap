# Spatial Intelligence Architecture

## Scope and analytical unit

The existing model remains **locality × quarter**. Spatial Intelligence adds an H3 zone context and a time-aware infrastructure feature layer; it does not replace the local model with a cell × quarter price model.

```text
locality price signal (only if verified)
             +
H3 zone + locality assignment + temporal infrastructure features
             ↓
truthful price taxonomy and spatial readiness
```

`CELL_MODEL_ESTIMATE` and `LOCALITY_ANCHORED_CELL_ESTIMATE` are reserved taxonomy states. They are not emitted by the current implementation because no fitted and validated cell adjustment exists.

## Geometry and persistence

`config/spatial.yaml` owns H3 resolution and coverage settings. The supported area is a reproducible union of metric buffers around the registry centroids in `config/localities.yaml`. This strategy carries the limitation that it is coverage, not an administrative or locality-boundary geometry.

The versioned PostgreSQL migration creates:

- `spatial_geometry_sources` for source, source reference, retrieval date, and licence notes;
- `spatial_cells` for H3 ID, `geometry(Polygon,4326)`, `centroid(Point,4326)`, locality context, and assignment provenance;
- `infrastructure_geometries` for the source geometry needed by the feature pipeline; and
- `cell_infrastructure_features` for a cell-quarter-version feature record.

The local SQLite environment stores WKT with explicit SRID columns so it can run without SpatiaLite. PostgreSQL production must use `sql/migrations/001_spatial_price_intelligence.sql`, which enables PostGIS and adds the GiST geometry indexes. The H3 unique constraint prevents duplicate cells; locality, region, and cell-quarter indexes support common query paths.

## Cell-locality mapping

There are no reliable locality polygons in this repository. The service therefore uses `NEAREST_CENTROID_FALLBACK`, preserves the assignment distance and quality class, and leaves a cell `UNASSIGNED` when it exceeds the configured distance gate. It never labels this value model confidence. If verified locality polygons arrive later, the priority is: polygon containment, majority overlap, then the existing centroid fallback.

## Temporal infrastructure features

The feature pipeline reuses `get_project_stage_at_quarter`. Event date and public release date must both be no later than the requested quarter. Geometry availability is checked independently. Distance semantics are documented in [spatial_distance_semantics.md](spatial_distance_semantics.md).

The current Phase-0 coordinate lists are explicitly mock script inputs. They are excluded from the spatial layer. Consequently, current production-style responses mark infrastructure metrics unavailable until verified geometry records are imported.

## Price and readiness taxonomy

Possible output levels are:

| Estimate type | Meaning |
| --- | --- |
| `PARCEL_VERIFIED` | Reserved for verified parcel-level valuation/transaction data. Not implemented. |
| `CELL_MODEL_ESTIMATE` | Reserved for a validated cell-trained model. Not implemented. |
| `LOCALITY_ANCHORED_CELL_ESTIMATE` | Reserved for a validated locality baseline plus spatial adjustment. Not implemented. |
| `LOCALITY_LEVEL_ESTIMATE_ONLY` | A verified locality signal, explicitly not a cell prediction. |
| `PRICE_SIGNAL_ONLY` | A non-estimate signal suitable for future evidence display. Reserved. |
| `SPATIAL_ESTIMATE_NOT_AVAILABLE` | No value is safe to show. |

Spatial readiness is categorical: `FULL_SPATIAL_ESTIMATE`, `LOCALITY_ANCHORED_ONLY`, `INFRASTRUCTURE_INTELLIGENCE_ONLY`, or `UNSUPPORTED`. It gates on locality assignment, verified non-synthetic price serving, verified geometry, and spatial-adjustment support. It is separate from locality Data Readiness, confidence intervals, and evidence strength.

## Scenario integration

The existing `ScenarioForecaster` takes locality features. The spatial adapter therefore returns `scenario_scope: LOCALITY_MODEL_WITH_SPATIAL_CONTEXT` and does not invoke a cell-trained scenario forecast. A caller can pass the locality ID and cell infrastructure context into the existing scenario workflow, but no spatial scenario adjustment is implied.
