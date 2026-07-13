# H3 Resolution Decision

## Decision

NiveshMap selects **H3 resolution 7** in `config/spatial.yaml`. The configured supported area is the union of 3 km buffers around the existing Phase-0 locality centroids. It is a coverage geometry, not a locality-boundary dataset.

The counts below were calculated from that exact documented coverage geometry on 2026-07-13 with H3 4.5.0. H3 average areas are global averages; local cell areas differ slightly.

| Resolution | Average cell area | Cells in current coverage | Urban interpretation | Assessment |
| --- | ---: | ---: | --- | --- |
| 6 | 36.129 km² | 11 | Broad sub-city / multi-locality zone | Too coarse to distinguish materially different infrastructure exposure around the registered NCR centres. |
| 7 | 5.161 km² | 76 | Zone-scale urban analytical cell | Selected. It can show infrastructure exposure without resembling a parcel grid. |
| 8 | 0.737 km² | 508 | Neighbourhood / block-scale visual cell | False-precision risk is high because localities have only centroid context and price data is not cell-level. It also increases geometry and viewport payload costs about sevenfold. |

## Why resolution 7

At resolution 7, the grid is small enough that a nearby station or corridor can vary across cells, but is still unmistakably a zone rather than a plot. The selected grid remains manageable as GeoJSON: the current locality-coverage strategy generates only 76 cells. Viewport filtering and a 500-cell response limit are nevertheless part of the contract for future coverage expansion.

The current price signal is locality × quarter and the generated Phase-0 panel is synthetic. Resolution 7 therefore does **not** authorize per-cell price differentiation. Until a validated spatial adjustment is trained, each cell either reports `LOCALITY_LEVEL_ESTIMATE_ONLY` for a verified locality signal or `SPATIAL_ESTIMATE_NOT_AVAILABLE`.

## Future migration strategy

The resolution is configuration-owned, never scattered across code. A resolution change should:

1. create a new `feature_version` and regenerate cells from the same recorded coverage geometry;
2. recompute cell-locality mappings and time-aware infrastructure features;
3. preserve prior H3 rows for reproducibility rather than overwriting historical feature records;
4. revalidate output taxonomy and frontend legends before exposing the new grid.
