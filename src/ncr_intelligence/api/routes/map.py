"""Map spatial intelligence HTTP routes."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from ...geospatial.spatial_intelligence import SpatialIntelligenceService, SpatialLayerError
from ..dependencies import get_spatial_service
from ..errors import internal_spatial_error_payload, spatial_error_payload, spatial_error_status_code
from ..validation import CoordinateValidationError, parse_latitude, parse_longitude, parse_viewport_bounds

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/map", tags=["map"])


def _validation_error_response(exc: CoordinateValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def _quarter_error_response(exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "INVALID_COORDINATES", "message": str(exc)}},
    )


@router.get("/cell")
def get_map_cell(
    lat: Optional[str] = Query(None),
    lon: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    scenario: Optional[str] = Query(None),
    service: SpatialIntelligenceService = Depends(get_spatial_service),
):
    """Resolve a map click to a spatial intelligence payload."""
    try:
        latitude = parse_latitude(lat)
        longitude = parse_longitude(lon)
        return service.get_cell(latitude, longitude, quarter=quarter, scenario=scenario)
    except CoordinateValidationError as exc:
        return _validation_error_response(exc)
    except SpatialLayerError as exc:
        return JSONResponse(
            status_code=spatial_error_status_code(exc),
            content=spatial_error_payload(exc),
        )
    except ValueError as exc:
        return _quarter_error_response(exc)
    except Exception:
        logger.exception("Unhandled error in GET /api/map/cell")
        return JSONResponse(status_code=500, content=internal_spatial_error_payload())


@router.get("/cells")
def get_map_cells(
    min_lat: Optional[str] = Query(None),
    min_lon: Optional[str] = Query(None),
    max_lat: Optional[str] = Query(None),
    max_lon: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    zoom: Optional[str] = Query(None),
    service: SpatialIntelligenceService = Depends(get_spatial_service),
):
    """Return viewport cells whose centroids fall inside the requested bounds."""
    del zoom  # Accepted for frontend compatibility; resolution remains fixed at H3-7.
    try:
        bounds = parse_viewport_bounds(min_lat, min_lon, max_lat, max_lon)
        return service.get_cells(*bounds, quarter=quarter)
    except CoordinateValidationError as exc:
        return _validation_error_response(exc)
    except SpatialLayerError as exc:
        return JSONResponse(
            status_code=spatial_error_status_code(exc),
            content=spatial_error_payload(exc),
        )
    except ValueError as exc:
        return _quarter_error_response(exc)
    except Exception:
        logger.exception("Unhandled error in GET /api/map/cells")
        return JSONResponse(status_code=500, content=internal_spatial_error_payload())
