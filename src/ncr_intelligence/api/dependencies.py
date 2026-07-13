"""Shared service dependencies for the HTTP adapter."""

from __future__ import annotations

from functools import lru_cache
from typing import Callable

from fastapi import Request

from ..geospatial.spatial_intelligence import SpatialIntelligenceService

_SERVICE_STATE_KEY = "spatial_intelligence_service"


def get_spatial_service(request: Request) -> SpatialIntelligenceService:
    """Return the application-scoped spatial service instance."""
    service = getattr(request.app.state, _SERVICE_STATE_KEY, None)
    if service is None:
        raise RuntimeError("SpatialIntelligenceService is not configured on the application.")
    return service


from shapely.wkt import loads as wkt_loads
from src.ncr_intelligence.database.connection import get_db_session
from src.ncr_intelligence.database.models import (
    PropertyPriceObservation,
    InfrastructureProject,
    InfrastructureEvent,
    InfrastructureGeometry
)
from src.ncr_intelligence.geospatial.spatial_intelligence import LocalityPriceSignal, InfrastructureAsset

def load_price_signals_from_db() -> list[LocalityPriceSignal]:
    """Load verified price signals from property_price_observations."""
    session = get_db_session()
    try:
        obs = session.query(PropertyPriceObservation).all()
        signals = []
        for o in obs:
            # Verify circle rates and non-synthetic, non-proxy observations
            is_circle = o.price_type == "CIRCLE_RATE" or "circle" in o.price_type.lower()
            verified = is_circle or (not o.is_proxy and o.price_type in {"COMPOSITE_PRICE_PROXY", "RERA_ESTIMATE"})
            signals.append(LocalityPriceSignal(
                locality_id=o.locality_id,
                quarter=o.quarter,
                price_signal_type=o.price_type,
                value=float(o.price_value) if o.price_value is not None else None,
                unit=o.price_unit,
                verified_for_spatial_serving=verified,
                is_synthetic=o.is_proxy,
                source_reference=o.raw_reference or f"Observation ID {o.observation_id}"
            ))
        return signals
    except Exception:
        return []
    finally:
        session.close()

def load_infrastructure_assets_from_db() -> list[InfrastructureAsset]:
    """Load infrastructure assets and their time-aware stage events from the database."""
    session = get_db_session()
    try:
        projects = session.query(InfrastructureProject).all()
        assets = []
        for p in projects:
            # Query geometries
            geom_records = session.query(InfrastructureGeometry).filter_by(project_id=p.project_id).all()
            
            # Extract stage events
            events = []
            for e in p.events:
                events.append({
                    "stage": e.stage,
                    "event_date": e.event_date,
                    "article_publish_date": e.article_publish_date
                })
                
            if geom_records:
                for gr in geom_records:
                    try:
                        geom = wkt_loads(gr.geometry)
                    except Exception:
                        geom = None
                    assets.append(InfrastructureAsset(
                        project_id=p.project_id,
                        project_type=p.project_type,
                        geometry=geom,
                        stage_events=events,
                        geometry_available_date=gr.geometry_available_date,
                        geometry_quality_class=gr.geometry_quality_class,
                        geometry_role=gr.geometry_role,
                        source_reference=gr.notes
                    ))
            else:
                assets.append(InfrastructureAsset(
                    project_id=p.project_id,
                    project_type=p.project_type,
                    geometry=None,
                    stage_events=events,
                    geometry_available_date=None,
                    geometry_quality_class="UNKNOWN",
                    geometry_role="UNKNOWN",
                    source_reference=None
                ))
        return assets
    except Exception:
        return []
    finally:
        session.close()

@lru_cache
def build_default_spatial_service() -> SpatialIntelligenceService:
    """Construct the default production spatial service once per process, seeding it from the DB."""
    price_signals = load_price_signals_from_db()
    infra_assets = load_infrastructure_assets_from_db()
    return SpatialIntelligenceService(
        price_signals=price_signals,
        infrastructure_assets=infra_assets
    )


def configure_spatial_service(app, service_factory: Callable[[], SpatialIntelligenceService] | None = None) -> None:
    """Attach a spatial service factory to application state."""
    factory = service_factory or build_default_spatial_service
    app.state.spatial_service_factory = factory
    app.state.spatial_intelligence_service = factory()
