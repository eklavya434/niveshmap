-- DDL for NCR Infrastructure-Driven Real Estate Platform (Phase 0)

-- Drop tables if they exist (for clean initialization/testing)
DROP TABLE IF EXISTS data_readiness_results CASCADE;
DROP TABLE IF EXISTS project_locality_links CASCADE;
DROP TABLE IF EXISTS infrastructure_events CASCADE;
DROP TABLE IF EXISTS infrastructure_projects CASCADE;
DROP TABLE IF EXISTS property_price_observations CASCADE;
DROP TABLE IF EXISTS source_audit_results CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;
DROP TABLE IF EXISTS localities CASCADE;

-- 1. Localities Table
CREATE TABLE localities (
    locality_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(100) NOT NULL, -- Delhi, Noida, Noida West, Gurugram, etc.
    state_or_ut VARCHAR(50) NOT NULL,
    district VARCHAR(100) NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    urban_maturity_class VARCHAR(50) NOT NULL CHECK (urban_maturity_class IN ('MATURE', 'TRANSITIONAL', 'EMERGING')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_lat CHECK (latitude BETWEEN 28.0 AND 29.0), -- Delhi NCR bounds validation
    CONSTRAINT check_lon CHECK (longitude BETWEEN 76.5 AND 78.0)
);

-- 2. Data Sources Table
CREATE TABLE data_sources (
    source_id VARCHAR(50) PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_category VARCHAR(100) NOT NULL, -- baseline, rera, circle_rates, infrastructure, etc.
    geography VARCHAR(100) NOT NULL,
    official_source BOOLEAN DEFAULT TRUE,
    source_url VARCHAR(500),
    access_method VARCHAR(50) NOT NULL, -- api, html, pdf, manual_download
    expected_format VARCHAR(50) NOT NULL, -- csv, json, html, pdf, xlsx
    historical_depth_notes TEXT,
    legal_access_notes TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- 3. Source Audit Results Table
CREATE TABLE source_audit_results (
    audit_id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) NOT NULL REFERENCES data_sources(source_id) ON DELETE CASCADE,
    audit_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accessible BOOLEAN NOT NULL,
    records_found INTEGER DEFAULT 0,
    earliest_date_found DATE,
    latest_date_found DATE,
    structured_data_available BOOLEAN DEFAULT FALSE,
    manual_intervention_required BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- 4. Property Price Observations Table
CREATE TABLE property_price_observations (
    observation_id SERIAL PRIMARY KEY,
    locality_id VARCHAR(50) NOT NULL REFERENCES localities(locality_id) ON DELETE CASCADE,
    observation_date DATE NOT NULL,
    quarter VARCHAR(10) NOT NULL, -- format 'YYYY-Q#' e.g., '2022-Q3'
    price_value NUMERIC(15, 2) NOT NULL,
    price_unit VARCHAR(50) NOT NULL, -- e.g., 'INR/sqft', 'INR/sqm'
    price_type VARCHAR(50) NOT NULL, -- transaction, listing, circle_rate, rera_disclosure, index, proxy
    source_id VARCHAR(50) NOT NULL REFERENCES data_sources(source_id),
    source_quality_class VARCHAR(50) NOT NULL, -- e.g., HIGH, MEDIUM, LOW
    is_proxy BOOLEAN DEFAULT FALSE,
    raw_reference TEXT,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Infrastructure Projects Table
CREATE TABLE infrastructure_projects (
    project_id VARCHAR(100) PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    project_type VARCHAR(50) NOT NULL, -- METRO, RRTS, EXPRESSWAY_HIGHWAY, AIRPORT
    primary_authority VARCHAR(100) NOT NULL, -- DMRC, NMRC, NHAI, YEIDA, NCRTC, etc.
    description TEXT,
    current_stage VARCHAR(50) NOT NULL, -- PROPOSED, APPROVED, CONTRACTED, UNDER_CONSTRUCTION, OPERATIONAL, STALLED_DELAYED_CANCELLED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Infrastructure Events Table
CREATE TABLE infrastructure_events (
    event_id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL REFERENCES infrastructure_projects(project_id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL, -- normalized stage
    raw_stage_text VARCHAR(255),
    event_date DATE NOT NULL,
    article_publish_date DATE,
    evidence_source_id VARCHAR(50) NOT NULL REFERENCES data_sources(source_id),
    evidence_strength NUMERIC(3, 2) NOT NULL CHECK (evidence_strength BETWEEN 0.0 AND 1.0), -- confidence score
    evidence_phrase TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Project Locality Links Table (Many-to-Many proximity relationship)
CREATE TABLE project_locality_links (
    project_id VARCHAR(100) REFERENCES infrastructure_projects(project_id) ON DELETE CASCADE,
    locality_id VARCHAR(50) REFERENCES localities(locality_id) ON DELETE CASCADE,
    distance_km NUMERIC(6, 2) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL, -- e.g., 'direct_exposure', 'influence_zone', 'nearest_station'
    PRIMARY KEY (project_id, locality_id)
);

-- 8. Data Readiness Results Table
CREATE TABLE data_readiness_results (
    readiness_id SERIAL PRIMARY KEY,
    locality_id VARCHAR(50) NOT NULL REFERENCES localities(locality_id) ON DELETE CASCADE,
    audit_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    price_coverage_score NUMERIC(5, 2) NOT NULL,
    price_source_quality_score NUMERIC(5, 2) NOT NULL,
    quarterly_observation_score NUMERIC(5, 2) NOT NULL,
    infrastructure_history_score NUMERIC(5, 2) NOT NULL,
    infrastructure_evidence_score NUMERIC(5, 2) NOT NULL,
    geospatial_completeness_score NUMERIC(5, 2) NOT NULL,
    analogue_depth_score NUMERIC(5, 2) NOT NULL,
    socioeconomic_completeness_score NUMERIC(5, 2) NOT NULL,
    overall_readiness_score NUMERIC(5, 2) NOT NULL,
    readiness_class VARCHAR(50) NOT NULL, -- FULL_FORECAST_ELIGIBLE, LIMITED_FORECAST_ELIGIBLE, INTELLIGENCE_ONLY, INSUFFICIENT_COVERAGE
    forecast_eligibility VARCHAR(255) NOT NULL,
    failure_reasons TEXT
);

-- Create Indexes for optimization
CREATE INDEX idx_price_observations_locality_quarter ON property_price_observations(locality_id, quarter);
CREATE INDEX idx_infra_events_project ON infrastructure_events(project_id);
CREATE INDEX idx_project_locality_links_locality ON project_locality_links(locality_id);
CREATE INDEX idx_readiness_locality ON data_readiness_results(locality_id);
