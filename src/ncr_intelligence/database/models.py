from sqlalchemy import Column, String, Numeric, Boolean, Integer, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from .connection import Base

# SQLAlchemy Declarative Models matching sql/schema.sql

class Locality(Base):
    __tablename__ = 'localities'
    
    locality_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    region = Column(String(100), nullable=False)
    state_or_ut = Column(String(50), nullable=False)
    district = Column(String(100), nullable=False)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    urban_maturity_class = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    price_observations = relationship("PropertyPriceObservation", back_populates="locality", cascade="all, delete-orphan")
    project_links = relationship("ProjectLocalityLink", back_populates="locality", cascade="all, delete-orphan")
    readiness_results = relationship("DataReadinessResult", back_populates="locality", cascade="all, delete-orphan")


class DataSource(Base):
    __tablename__ = 'data_sources'
    
    source_id = Column(String(50), primary_key=True)
    source_name = Column(String(255), nullable=False)
    source_category = Column(String(100), nullable=False)
    geography = Column(String(100), nullable=False)
    official_source = Column(Boolean, default=True)
    source_url = Column(String(500))
    access_method = Column(String(50), nullable=False)
    expected_format = Column(String(50), nullable=False)
    historical_depth_notes = Column(Text)
    legal_access_notes = Column(Text)
    active = Column(Boolean, default=True)


class SourceAuditResult(Base):
    __tablename__ = 'source_audit_results'
    
    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), ForeignKey('data_sources.source_id', ondelete='CASCADE'), nullable=False)
    audit_date = Column(DateTime(timezone=True), server_default=func.now())
    accessible = Column(Boolean, nullable=False)
    records_found = Column(Integer, default=0)
    earliest_date_found = Column(Date)
    latest_date_found = Column(Date)
    structured_data_available = Column(Boolean, default=False)
    manual_intervention_required = Column(Boolean, default=False)
    notes = Column(Text)


class PropertyPriceObservation(Base):
    __tablename__ = 'property_price_observations'
    
    observation_id = Column(Integer, primary_key=True, autoincrement=True)
    locality_id = Column(String(50), ForeignKey('localities.locality_id', ondelete='CASCADE'), nullable=False)
    observation_date = Column(Date, nullable=False)
    quarter = Column(String(10), nullable=False)
    price_value = Column(Numeric(15, 2), nullable=False)
    price_unit = Column(String(50), nullable=False)
    price_type = Column(String(50), nullable=False)
    source_id = Column(String(50), ForeignKey('data_sources.source_id'), nullable=False)
    source_quality_class = Column(String(50), nullable=False)
    is_proxy = Column(Boolean, default=False)
    raw_reference = Column(Text)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    locality = relationship("Locality", back_populates="price_observations")


class InfrastructureProject(Base):
    __tablename__ = 'infrastructure_projects'
    
    project_id = Column(String(100), primary_key=True)
    project_name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False)
    project_type = Column(String(50), nullable=False)
    primary_authority = Column(String(100), nullable=False)
    description = Column(Text)
    current_stage = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    events = relationship("InfrastructureEvent", back_populates="project", cascade="all, delete-orphan")
    locality_links = relationship("ProjectLocalityLink", back_populates="project", cascade="all, delete-orphan")


class InfrastructureEvent(Base):
    __tablename__ = 'infrastructure_events'
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(100), ForeignKey('infrastructure_projects.project_id', ondelete='CASCADE'), nullable=False)
    stage = Column(String(50), nullable=False)
    raw_stage_text = Column(String(255))
    event_date = Column(Date, nullable=False)
    article_publish_date = Column(Date)
    evidence_source_id = Column(String(50), ForeignKey('data_sources.source_id'), nullable=False)
    evidence_strength = Column(Numeric(3, 2), nullable=False)
    evidence_phrase = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("InfrastructureProject", back_populates="events")


class ProjectLocalityLink(Base):
    __tablename__ = 'project_locality_links'
    
    project_id = Column(String(100), ForeignKey('infrastructure_projects.project_id', ondelete='CASCADE'), primary_key=True)
    locality_id = Column(String(50), ForeignKey('localities.locality_id', ondelete='CASCADE'), primary_key=True)
    distance_km = Column(Numeric(6, 2), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    
    # Relationships
    project = relationship("InfrastructureProject", back_populates="locality_links")
    locality = relationship("Locality", back_populates="project_links")


class DataReadinessResult(Base):
    __tablename__ = 'data_readiness_results'
    
    readiness_id = Column(Integer, primary_key=True, autoincrement=True)
    locality_id = Column(String(50), ForeignKey('localities.locality_id', ondelete='CASCADE'), nullable=False)
    audit_date = Column(DateTime(timezone=True), server_default=func.now())
    price_coverage_score = Column(Numeric(5, 2), nullable=False)
    price_source_quality_score = Column(Numeric(5, 2), nullable=False)
    quarterly_observation_score = Column(Numeric(5, 2), nullable=False)
    infrastructure_history_score = Column(Numeric(5, 2), nullable=False)
    infrastructure_evidence_score = Column(Numeric(5, 2), nullable=False)
    geospatial_completeness_score = Column(Numeric(5, 2), nullable=False)
    analogue_depth_score = Column(Numeric(5, 2), nullable=False)
    socioeconomic_completeness_score = Column(Numeric(5, 2), nullable=False)
    overall_readiness_score = Column(Numeric(5, 2), nullable=False)
    readiness_class = Column(String(50), nullable=False)
    forecast_eligibility = Column(String(255), nullable=False)
    failure_reasons = Column(Text)
    
    # Relationships
    locality = relationship("Locality", back_populates="readiness_results")
