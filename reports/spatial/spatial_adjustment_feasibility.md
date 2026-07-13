# Spatial Adjustment Feasibility

## Verdict

**No cell-level price adjustment is currently defensible.** The selected approach is **E — no cell-level price adjustment yet**.

## Evidence audit

| Requirement | Repository evidence | Decision |
| --- | --- | --- |
| Locality price signal | The Phase-0 panel is generated with mock price trends for feasibility testing. It is not a production-verified price-serving dataset. | Block numeric spatial serving by default. |
| Parcel or cell price labels | None. | No parcel or cell model can be trained. |
| Locality polygons | None; the registry contains centroids. | Only a labelled nearest-centroid fallback is available. |
| Infrastructure geometries | Existing coordinates are mock point lists in scripts; no source-backed station or corridor geometry table exists. | Do not calculate real map distances from them. |
| Temporal event method | `get_project_stage_at_quarter` correctly checks event and publication dates. | Reuse in the new feature pipeline. |
| Existing forecaster | Locality-trained scenario model with locality feature inputs. | Keep scenario scope locality-trained. |

## Methods evaluated

- Transparent regression spatial adjustment: blocked by no observed cell-level prices and no verified geometry features.
- Residual model: blocked by no residual target at cell grain.
- Hierarchical model: blocked by no lower-level observations or defensible locality boundaries.
- Gradient-boosting residual correction: blocked for the same target/data reasons and would reduce interpretability.
- No adjustment: selected. It preserves existing locality methodology and exposes spatial readiness/feature availability without manufacturing variation.

## Current output

The spatial service can return `LOCALITY_LEVEL_ESTIMATE_ONLY` only when a caller supplies a non-synthetic, provenance-approved locality signal. It returns `SPATIAL_ESTIMATE_NOT_AVAILABLE` for the present repository data. This is intentional.

## Required evidence before reconsideration

1. source-backed locality polygons or a defensible coverage/mapping alternative;
2. historical, provenance-approved price observations at a finer geography or a study design supporting within-locality effects;
3. time-versioned station points, route lines, and airport reference geometry;
4. out-of-time validation, uncertainty reporting, and a documented causal/associational interpretation;
5. review of whether resolution 7 remains appropriate once price granularity improves.
