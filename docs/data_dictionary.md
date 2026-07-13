# Data Dictionary

## 1. Relational Database Tables

### `localities`
- `locality_id` (VARCHAR(50), Primary Key): Unique alphanumeric ID for the locality.
- `name` (VARCHAR(255)): Name of the locality.
- `region` (VARCHAR(100)): Target NCR administrative region.
- `state_or_ut` (VARCHAR(50)): Delhi, Uttar Pradesh, or Haryana.
- `district` (VARCHAR(100)): District name.
- `latitude` (NUMERIC(9,6)): Center latitude coordinate.
- `longitude` (NUMERIC(9,6)): Center longitude coordinate.
- `urban_maturity_class` (VARCHAR(50)): `MATURE`, `TRANSITIONAL`, or `EMERGING`.

### `property_price_observations`
- `observation_id` (SERIAL, Primary Key): Autoincrement identifier.
- `locality_id` (VARCHAR(50), Foreign Key): References `localities.locality_id`.
- `observation_date` (DATE): Timestamp of the observation.
- `quarter` (VARCHAR(10)): Calendar quarter (`YYYY-Q#`).
- `price_value` (NUMERIC(15,2)): Price valuation or index value.
- `price_unit` (VARCHAR(50)): E.g., `INR/sqft`, `index_ratio`.
- `price_type` (VARCHAR(50)): E.g., `circle_rate`, `transaction`, `rera_disclosure`, `index`.
- `source_id` (VARCHAR(50)): References `data_sources.source_id`.
- `source_quality_class` (VARCHAR(50)): `HIGH`, `MEDIUM`, or `LOW`.
- `is_proxy` (BOOLEAN): True if composite or baseline index.

### `infrastructure_projects`
- `project_id` (VARCHAR(100), Primary Key): Unique identifier.
- `project_name` (VARCHAR(255)): Human-readable name.
- `normalized_name` (VARCHAR(255)): Lowercase, underscore separated.
- `project_type` (VARCHAR(50)): `METRO`, `RRTS`, `EXPRESSWAY_HIGHWAY`, or `AIRPORT`.
- `primary_authority` (VARCHAR(100)): E.g., `DMRC`, `NHAI`.
- `current_stage` (VARCHAR(50)): Current active stage enum.

### `infrastructure_events`
- `event_id` (SERIAL, Primary Key): Autoincrement identifier.
- `project_id` (VARCHAR(100), Foreign Key): References `infrastructure_projects.project_id`.
- `stage` (VARCHAR(50)): Normalized stage enum.
- `raw_stage_text` (VARCHAR(255)): Event phrase in source document.
- `event_date` (DATE): Date of the physical milestone.
- `article_publish_date` (DATE): Public release date.
- `evidence_strength` (NUMERIC(3,2)): Confidence index (0.0 to 1.0).

---

## 2. Processed Output Panels

### `phase0_quarterly_panel.csv`
- `locality_id` (str): References candidate locality.
- `quarter` (str): Calendar quarter (`YYYY-Q#`).
- `region` (str): Geographic region.
- `price_proxy` (float): Derived price proxy in INR/sqft.
- `metro_stage` / `expressway_stage` / `airport_stage` / `rrts_stage` (str): Reconstructed status as of that quarter.
- `distance_nearest_operational_metro_km` (float): Spatial distance to closest active station.
- `distance_airport_km` (float): Spatial distance to Jewar or IGI Airport.
- `data_readiness_score` (float): Dynamic score from readiness framework.
