# Map Frontend Handoff

Concise integration guide for the visual map agent (Antigravity). Backend spatial logic lives in `SpatialIntelligenceService`; the HTTP adapter is a thin wrapper only.

## Base URL

Default local development:

```text
http://localhost:8000
```

Start the adapter:

```bash
python api_server.py
```

## Endpoints

### 1. Cell click — `GET /api/map/cell`

**Example**

```http
GET /api/map/cell?lat=28.6186&lon=77.3719&quarter=2025-Q4
```

| Parameter | Required | Notes |
| --- | --- | --- |
| `lat` | yes | WGS84 latitude, `-90` … `90` |
| `lon` | yes | WGS84 longitude, `-180` … `180` |
| `quarter` | no | `YYYY-Q#`; defaults to current calendar quarter |
| `scenario` | no | Passed through to service; scenario output remains `NOT_EVALUATED` |

**Success (HTTP 200)** — key fields:

- `cell.h3_index`, `cell.geometry` (GeoJSON polygon), `cell.spatial_readiness`
- `locality.locality_id`, `locality.name`, `locality.region`
- `price_intelligence.estimate_type`, `price_intelligence.value` (nullable)
- `infrastructure.*` distance/count metrics (mostly null until verified geometry is loaded)
- `data_quality.limitations`, `data_quality.feature_statuses`
- `scenario` (null unless `scenario` query param supplied)

**Unsupported location (HTTP 422)**

```json
{"error": {"code": "OUTSIDE_SUPPORTED_GEOGRAPHY", "message": "..."}}
```

**Invalid coordinates (HTTP 400)**

```json
{"error": {"code": "INVALID_COORDINATES", "message": "..."}}
```

### 2. Viewport cells — `GET /api/map/cells`

**Example**

```http
GET /api/map/cells?min_lat=28.60&min_lon=77.35&max_lat=28.64&max_lon=77.40&quarter=2025-Q4
```

| Parameter | Required | Notes |
| --- | --- | --- |
| `min_lat`, `min_lon`, `max_lat`, `max_lon` | yes | Bounding box; min must be strictly less than max |
| `quarter` | no | `YYYY-Q#` |
| `zoom` | no | Accepted for compatibility; **does not change H3 resolution (fixed at 7)** |

**Success (HTTP 200)**

- `returned_cells` — count in this response
- `cells[]` — same per-cell shape as `/api/map/cell` (without top-level `location`)
- Empty viewport: HTTP 200 with `returned_cells: 0` and `cells: []`

**Query failure (HTTP 500)**

```json
{"error": {"code": "SPATIAL_LAYER_ERROR", "message": "..."}}
```

## Spatial readiness states

| State | Render guidance |
| --- | --- |
| `LOCALITY_ANCHORED_ONLY` | Locality-level price signal may exist; label as locality-level, not parcel/cell valuation |
| `INFRASTRUCTURE_INTELLIGENCE_ONLY` | Show infrastructure metrics; **no price colour** |
| `UNSUPPORTED` | Neutral/unsupported styling; **no price colour** |
| `FULL_SPATIAL_ESTIMATE` | Reserved for future validated cell adjustment (not emitted today) |

## Estimate types

| `estimate_type` | Numeric price allowed? |
| --- | --- |
| `SPATIAL_ESTIMATE_NOT_AVAILABLE` | **No** — `value` is null |
| `LOCALITY_LEVEL_ESTIMATE_ONLY` | **Yes** — locality-level signal only; must be labelled clearly |
| `INFRASTRUCTURE_INTELLIGENCE_ONLY` | **No** (readiness state, not estimate type) |
| `PARCEL_VERIFIED`, `CELL_MODEL_ESTIMATE`, `LOCALITY_ANCHORED_CELL_ESTIMATE`, `PRICE_SIGNAL_ONLY` | Not emitted by current service |

## Price rendering rules

1. **Do not heatmap** cells where `estimate_type` is `SPATIAL_ESTIMATE_NOT_AVAILABLE`.
2. **Do not infer** prices from neighbours, infrastructure proximity, or locality defaults.
3. When `value` is non-null and `estimate_type` is `LOCALITY_LEVEL_ESTIMATE_ONLY`, display: *"Locality-level price signal — not a parcel or cell valuation."*
4. Treat `null` price as a valid analytical outcome (HTTP 200), not a client error.

## Loading and error behaviour

| Condition | HTTP | UI action |
| --- | ---: | --- |
| Valid click inside coverage | 200 | Render cell polygon + panel from response |
| Click outside coverage | 422 | Show unsupported-location message; do not snap to nearest cell |
| Bad coordinates | 400 | Show validation message |
| Adapter/service failure | 500 | Show error state; do not show empty map as success |
| Empty viewport | 200 | Clear or dim cells; distinguish from 500 errors |

## Do not implement in the frontend

- H3 index calculation
- Spatial price adjustment or uplift heuristics
- Nearest-locality fallback for out-of-coverage clicks
- Fake heatmap scales for blocked estimate types

Use the API response fields verbatim for panel content.
