"""FastAPI application factory for the NiveshMap HTTP adapter."""

from __future__ import annotations

from typing import Callable

from fastapi import FastAPI

from ..geospatial.spatial_intelligence import SpatialIntelligenceService
from .dependencies import configure_spatial_service
from .routes import map as map_routes


def create_app(
    service_factory: Callable[[], SpatialIntelligenceService] | None = None,
) -> FastAPI:
    """Create the map API application.

    The repository is Streamlit-first; this adapter exposes spatial operations
    over HTTP without duplicating domain logic.
    """
    app = FastAPI(
        title="NiveshMap Spatial API",
        version="0.1.0",
        description=(
            "Thin HTTP adapter over SpatialIntelligenceService. "
            "Cell-level price adjustment remains blocked unless explicitly verified."
        ),
    )
    configure_spatial_service(app, service_factory=service_factory)
    app.include_router(map_routes.router)
    return app
