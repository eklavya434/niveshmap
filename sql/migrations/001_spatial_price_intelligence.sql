-- Spatial Price Intelligence Layer
-- Apply after sql/schema.sql on PostgreSQL. This migration is idempotent and
-- requires a PostgreSQL role permitted to create the postgis extension.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS spatial_geometry_sources (
    source_id VARCHAR(100) PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_reference VARCHAR(1000) NOT NULL,
    retrieval_date DATE NOT NULL,
    license_notes TEXT,
    geometry_strategy VARCHAR(100) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spatial_cells (
    cell_id VARCHAR(32) PRIMARY KEY,
    h3_index VARCHAR(32) NOT NULL UNIQUE,
    h3_resolution INTEGER NOT NULL,
    geometry geometry(Polygon, 4326) NOT NULL,
    centroid geometry(Point, 4326) NOT NULL,
    geometry_srid INTEGER NOT NULL DEFAULT 4326 CHECK (geometry_srid = 4326),
    centroid_srid INTEGER NOT NULL DEFAULT 4326 CHECK (centroid_srid = 4326),
    centroid_latitude NUMERIC(9, 6) NOT NULL,
    centroid_longitude NUMERIC(9, 6) NOT NULL,
    locality_id VARCHAR(50) REFERENCES localities(locality_id),
    region VARCHAR(100),
    state_or_ut VARCHAR(50),
    coverage_status VARCHAR(50) NOT NULL DEFAULT 'SUPPORTED',
    coordinate_source_id VARCHAR(100) REFERENCES spatial_geometry_sources(source_id),
    assignment_method VARCHAR(50) NOT NULL DEFAULT 'UNASSIGNED',
    assignment_distance_km NUMERIC(8, 3),
    assignment_quality_class VARCHAR(50) NOT NULL DEFAULT 'UNASSIGNED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- h3_index has a unique B-tree index from its constraint. The GiST index is
-- used by viewport / point geometry predicates, while locality and region
-- indexes support context and layer filtering.
CREATE INDEX IF NOT EXISTS idx_spatial_cells_geometry_gist ON spatial_cells USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_spatial_cells_locality ON spatial_cells (locality_id);
CREATE INDEX IF NOT EXISTS idx_spatial_cells_region ON spatial_cells (region);

CREATE TABLE IF NOT EXISTS infrastructure_geometries (
    geometry_id BIGSERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES infrastructure_projects(project_id) ON DELETE CASCADE,
    geometry_role VARCHAR(50) NOT NULL,
    geometry geometry(Geometry, 4326) NOT NULL,
    geometry_srid INTEGER NOT NULL DEFAULT 4326 CHECK (geometry_srid = 4326),
    geometry_quality_class VARCHAR(50) NOT NULL,
    geometry_available_date DATE,
    source_id VARCHAR(100) REFERENCES spatial_geometry_sources(source_id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_infrastructure_geometries_geometry_gist
    ON infrastructure_geometries USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_infrastructure_geometries_project
    ON infrastructure_geometries (project_id);

CREATE TABLE IF NOT EXISTS cell_infrastructure_features (
    cell_id VARCHAR(32) NOT NULL REFERENCES spatial_cells(cell_id) ON DELETE CASCADE,
    quarter VARCHAR(10) NOT NULL,
    feature_version VARCHAR(50) NOT NULL,
    nearest_operational_metro_km NUMERIC(8, 3),
    nearest_proposed_metro_km NUMERIC(8, 3),
    nearest_rrts_km NUMERIC(8, 3),
    nearest_expressway_highway_km NUMERIC(8, 3),
    airport_distance_km NUMERIC(8, 3),
    metro_count_3km INTEGER,
    metro_count_5km INTEGER,
    rrts_count_5km INTEGER,
    infra_count_3km INTEGER,
    infra_count_5km INTEGER,
    infra_count_10km INTEGER,
    active_project_count INTEGER,
    proposed_project_count INTEGER,
    under_construction_project_count INTEGER,
    operational_project_count INTEGER,
    feature_statuses JSONB NOT NULL DEFAULT '{}'::jsonb,
    unavailable_features JSONB NOT NULL DEFAULT '[]'::jsonb,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cell_id, quarter, feature_version)
);

CREATE INDEX IF NOT EXISTS idx_cell_infrastructure_features_cell_quarter
    ON cell_infrastructure_features (cell_id, quarter);
