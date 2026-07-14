"""Spatial client abstraction for HTTP API and Direct Mode."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
import logging

from src.ncr_intelligence.api.validation import (
    CoordinateValidationError,
    parse_latitude,
    parse_longitude,
    parse_viewport_bounds,
)
from src.ncr_intelligence.api.errors import (
    spatial_error_payload,
    internal_spatial_error_payload,
)
from src.ncr_intelligence.geospatial.spatial_intelligence import SpatialLayerError

logger = logging.getLogger(__name__)

class SpatialClient(ABC):
    """Abstract base class for accessing spatial intelligence data."""

    @abstractmethod
    def get_cell(
        self,
        lat: Any,
        lon: Any,
        quarter: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve single cell information by coordinates."""
        pass

    @abstractmethod
    def get_cells(
        self,
        min_lat: Any,
        min_lon: Any,
        max_lat: Any,
        max_lon: Any,
        quarter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve a list of cells within bounds."""
        pass


class HTTPSpatialClient(SpatialClient):
    """Client for accessing spatial intelligence over HTTP/FastAPI."""

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    def get_cell(
        self,
        lat: Any,
        lon: Any,
        quarter: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.api_base_url}/api/map/cell"
        params = {
            "lat": str(lat) if lat is not None else "",
            "lon": str(lon) if lon is not None else "",
        }
        if quarter:
            params["quarter"] = quarter
        if scenario:
            params["scenario"] = scenario

        try:
            response = requests.get(url, params=params, timeout=2.0)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 422 or response.status_code == 400:
                return response.json()
            else:
                return {"error": {"code": "HTTP_ERROR", "message": f"Status {response.status_code}"}}
        except Exception as exc:
            logger.exception("HTTP request failed in HTTPSpatialClient.get_cell")
            return {"error": {"code": "CONNECTION_ERROR", "message": str(exc)}}

    def get_cells(
        self,
        min_lat: Any,
        min_lon: Any,
        max_lat: Any,
        max_lon: Any,
        quarter: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.api_base_url}/api/map/cells"
        params = {
            "min_lat": str(min_lat) if min_lat is not None else "",
            "min_lon": str(min_lon) if min_lon is not None else "",
            "max_lat": str(max_lat) if max_lat is not None else "",
            "max_lon": str(max_lon) if max_lon is not None else "",
        }
        if quarter:
            params["quarter"] = quarter

        try:
            response = requests.get(url, params=params, timeout=2.0)
            if response.status_code == 200:
                return response.json()
            else:
                return {"cells": [], "returned_cells": 0}
        except Exception as exc:
            logger.exception("HTTP request failed in HTTPSpatialClient.get_cells")
            return {"cells": [], "returned_cells": 0, "error": str(exc)}


class DirectSpatialClient(SpatialClient):
    """Client for directly calling SpatialIntelligenceService without HTTP."""

    def __init__(self, service_factory=None):
        from src.ncr_intelligence.api.dependencies import build_default_spatial_service
        self.service_factory = service_factory or build_default_spatial_service

    def get_cell(
        self,
        lat: Any,
        lon: Any,
        quarter: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            latitude = parse_latitude(lat)
            longitude = parse_longitude(lon)
            service = self.service_factory()
            return service.get_cell(latitude, longitude, quarter=quarter, scenario=scenario)
        except CoordinateValidationError as exc:
            return {"error": {"code": exc.code, "message": exc.message}}
        except SpatialLayerError as exc:
            return spatial_error_payload(exc)
        except ValueError as exc:
            return {"error": {"code": "INVALID_COORDINATES", "message": str(exc)}}
        except Exception:
            logger.exception("Unhandled error in DirectSpatialClient.get_cell")
            return internal_spatial_error_payload()

    def get_cells(
        self,
        min_lat: Any,
        min_lon: Any,
        max_lat: Any,
        max_lon: Any,
        quarter: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            bounds = parse_viewport_bounds(min_lat, min_lon, max_lat, max_lon)
            service = self.service_factory()
            return service.get_cells(*bounds, quarter=quarter)
        except CoordinateValidationError as exc:
            return {"error": {"code": exc.code, "message": exc.message}}
        except SpatialLayerError as exc:
            return spatial_error_payload(exc)
        except ValueError as exc:
            return {"error": {"code": "INVALID_COORDINATES", "message": str(exc)}}
        except Exception:
            logger.exception("Unhandled error in DirectSpatialClient.get_cells")
            return {"cells": [], "returned_cells": 0}
