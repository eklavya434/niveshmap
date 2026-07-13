# Spatial Distance Semantics

All spatial distances are local metric-CRS measurements in EPSG:32643, returned in kilometres. They are not road travel time, walking time, or accessibility time.

| Feature | Required geometry | Semantics | Current status |
| --- | --- | --- |
| `nearest_operational_metro_km` | Station `Point` | Distance from cell centroid to the nearest station whose operational event and station geometry were publicly available by the requested quarter. | Unavailable until verified station geometry is loaded. |
| `nearest_proposed_metro_km` | Station `Point` | Distance to a station with a proposed/approved/contracted/under-construction status that was publicly evidenced by that quarter. | Unavailable until verified geometry is loaded. |
| `nearest_rrts_km` | Station `Point` or documented `LineString` / `MultiLineString` | Station distance is preferred when that is the project’s accepted analytical meaning; corridor distance is allowed only when documented. | Unavailable until verified geometry is loaded. |
| `nearest_expressway_highway_km` | Route `LineString` / `MultiLineString` | Minimum distance to the mapped corridor. A project centroid is rejected, not silently used as a proxy. | Unavailable until verified route geometry is loaded. |
| `airport_distance_km` | Documented airport `Point`, boundary `Polygon`, or `MultiPolygon` | Minimum distance to the documented reference geometry. The source must state whether it represents a terminal, official reference point, or boundary. | Unavailable until verified geometry is loaded. |

## Geometry quality and temporal integrity

`infrastructure_geometries` records geometry role, quality class, source, source reference, availability date, and SRID. A feature is calculated only when both conditions are true:

1. the project event is available as of the requested quarter under the existing `event_date` plus `article_publish_date` rule; and
2. the geometry itself was publicly available by that quarter.

If either source is absent, the response has `null` for the metric and an explicit `UNAVAILABLE` feature status. A low-quality geometry can be reported as `LOW_QUALITY_PROXY`, but it cannot be passed off as a corridor distance.
