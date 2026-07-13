# Map API Contract

The existing project has a Streamlit frontend and no HTTP backend. `SpatialIntelligenceService` implements the following transport-neutral operations now; an HTTP adapter should expose the same JSON contract as the routes below without duplicating analytical logic.

## `GET /api/map/cell`

Query parameters:

- `lat` and `lon` — required WGS84 coordinates;
- `quarter` — optional `YYYY-Q#`; defaults to the current calendar quarter until a production latest-valid-quarter resolver is introduced;
- `scenario` — optional existing scenario identifier.

`get_cell(lat, lon, quarter, scenario)` validates global coordinate ranges, rejects a point outside the documented coverage union with `OUTSIDE_SUPPORTED_GEOGRAPHY`, resolves a deterministic H3 cell, then returns locality assignment, price taxonomy, time-aware infrastructure features, readiness, and limitations.

Important response fields:

```json
{
  "cell": {
    "h3_index": "…",
    "resolution": 7,
    "geometry": {"type": "Polygon", "coordinates": []},
    "spatial_readiness": "UNSUPPORTED",
    "assignment_method": "NEAREST_CENTROID_FALLBACK"
  },
  "price_intelligence": {
    "estimate_type": "SPATIAL_ESTIMATE_NOT_AVAILABLE",
    "price_signal_type": null,
    "value": null,
    "unit": "INR_PER_SQFT",
    "as_of_quarter": "YYYY-Q#"
  },
  "infrastructure": {"nearest_operational_metro_km": null},
  "data_quality": {"limitations": []}
}
```

Cells must never be rendered as parcel valuations. A numeric price is present only with `LOCALITY_LEVEL_ESTIMATE_ONLY` or a future, separately validated estimate type.

## `GET /api/map/cells`

Query parameters: `min_lat`, `min_lon`, `max_lat`, `max_lon`, optional `quarter`, and optional `zoom` (accepted by a future HTTP adapter for frontend compatibility; it does not alter resolution in the current fixed-resolution layer).

`get_cells(min_lat, min_lon, max_lat, max_lon, quarter)` returns only cells whose **centroids** lie inside the viewport, applies the configured result limit, and returns GeoJSON polygons plus the same taxonomy/readiness fields as click analysis. It does not send the full NCR coverage for each request.

For PostgreSQL adapters, implement viewport filtering with `ST_Intersects` against the GiST-indexed cell geometry. The in-process and SQLite development service uses centroid bounds for portability; keep the response behaviour consistent.

## Errors

| Code | HTTP status | Meaning |
| --- | ---: | --- |
| `INVALID_COORDINATES` | 400 | Latitude, longitude, or viewport bounds are invalid, missing, non-numeric, NaN, infinite, or inverted. |
| `OUTSIDE_SUPPORTED_GEOGRAPHY` | 422 | The click is outside documented centroid-buffer coverage. Do not return a nearest NCR locality. |
| `SPATIAL_LAYER_ERROR` | 500 | Internal controlled spatial-layer error. Stack traces are not returned to clients. |

Successful analytical responses use HTTP 200 even when `price_intelligence.value` is null. A null price with `estimate_type: SPATIAL_ESTIMATE_NOT_AVAILABLE` is a valid analytical state, not an API failure.

## HTTP adapter

Run the adapter separately from Streamlit:

```bash
python api_server.py
# or
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

Routes are implemented in `src/ncr_intelligence/api/routes/map.py` and delegate directly to `SpatialIntelligenceService`.

## Visual-map integration

Render `LOCALITY_LEVEL_ESTIMATE_ONLY` differently from future cell model estimates. Cells with `SPATIAL_ESTIMATE_NOT_AVAILABLE` must not be assigned a surrogate numeric heatmap colour. Use `spatial_readiness`, `feature_statuses`, and `limitations` to show an infrastructure-intelligence or unsupported state.
