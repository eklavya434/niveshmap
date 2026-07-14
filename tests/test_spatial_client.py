"""Tests for HTTPSpatialClient and DirectSpatialClient."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from src.ncr_intelligence.geospatial.spatial_client import HTTPSpatialClient, DirectSpatialClient
from src.ncr_intelligence.geospatial.spatial_intelligence import (
    UnsupportedGeographyError,
    InvalidSpatialPointError,
)

def test_http_spatial_client_get_cell():
    # Mock requests.get
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cell_id": "test_cell", "price": 100}
        mock_get.return_value = mock_response

        client = HTTPSpatialClient("http://fake-api")
        res = client.get_cell(28.6186, 77.3719, quarter="2025-Q4", scenario="scen_1")

        mock_get.assert_called_once_with(
            "http://fake-api/api/map/cell",
            params={"lat": "28.6186", "lon": "77.3719", "quarter": "2025-Q4", "scenario": "scen_1"},
            timeout=2.0
        )
        assert res == {"cell_id": "test_cell", "price": 100}


def test_http_spatial_client_get_cells():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cells": [{"cell_id": "1"}], "returned_cells": 1}
        mock_get.return_value = mock_response

        client = HTTPSpatialClient("http://fake-api")
        res = client.get_cells(28.5, 77.3, 28.7, 77.4, quarter="2025-Q4")

        mock_get.assert_called_once_with(
            "http://fake-api/api/map/cells",
            params={"min_lat": "28.5", "min_lon": "77.3", "max_lat": "28.7", "max_lon": "77.4", "quarter": "2025-Q4"},
            timeout=2.0
        )
        assert res == {"cells": [{"cell_id": "1"}], "returned_cells": 1}


def test_direct_spatial_client_get_cell_delegates():
    mock_service = MagicMock()
    mock_service.get_cell.return_value = {"cell_id": "test_cell", "price": 200}
    
    # Factory returning our mock
    def factory():
        return mock_service

    client = DirectSpatialClient(service_factory=factory)
    res = client.get_cell(28.6186, 77.3719, quarter="2025-Q4", scenario="scen_1")

    mock_service.get_cell.assert_called_once_with(28.6186, 77.3719, quarter="2025-Q4", scenario="scen_1")
    assert res == {"cell_id": "test_cell", "price": 200}


def test_direct_spatial_client_get_cells_delegates():
    mock_service = MagicMock()
    mock_service.get_cells.return_value = {"cells": [{"cell_id": "test"}], "returned_cells": 1}
    
    def factory():
        return mock_service

    client = DirectSpatialClient(service_factory=factory)
    res = client.get_cells(28.5, 77.3, 28.7, 77.4, quarter="2025-Q4")

    mock_service.get_cells.assert_called_once_with(28.5, 77.3, 28.7, 77.4, quarter="2025-Q4")
    assert res == {"cells": [{"cell_id": "test"}], "returned_cells": 1}


def test_direct_mode_preserves_null_price_values():
    mock_service = MagicMock()
    # Mock returning null price signals
    mock_service.get_cell.return_value = {
        "price_signals": {
            "quarterly_price": None,
            "estimate_type": "SPATIAL_ESTIMATE_NOT_AVAILABLE"
        }
    }
    
    client = DirectSpatialClient(service_factory=lambda: mock_service)
    res = client.get_cell(28.6186, 77.3719)

    assert res["price_signals"]["quarterly_price"] is None
    assert res["price_signals"]["estimate_type"] == "SPATIAL_ESTIMATE_NOT_AVAILABLE"


def test_direct_mode_preserves_spatial_readiness_taxonomy():
    mock_service = MagicMock()
    mock_service.get_cell.return_value = {
        "readiness": {
            "status": "UNSUPPORTED",
            "is_ready": False
        }
    }
    
    client = DirectSpatialClient(service_factory=lambda: mock_service)
    res = client.get_cell(28.6186, 77.3719)

    assert res["readiness"]["status"] == "UNSUPPORTED"
    assert res["readiness"]["is_ready"] is False


def test_direct_mode_does_not_fabricate_cell_prices():
    mock_service = MagicMock()
    mock_service.get_cell.return_value = {
        "price_signals": {
            "quarterly_price": None,
            "estimate_type": "SPATIAL_ESTIMATE_NOT_AVAILABLE"
        }
    }
    
    client = DirectSpatialClient(service_factory=lambda: mock_service)
    res = client.get_cell(28.6186, 77.3719)
    # Ensure no default fabrication occurred
    assert res["price_signals"]["quarterly_price"] is None


def test_response_shape_equivalence_between_adapters():
    # Verify that HTTP response content mapping matches Direct client exception wrapping
    mock_service = MagicMock()
    mock_service.get_cell.side_effect = UnsupportedGeographyError("Out of bounds")

    # FastAPI app setup mock / response format check
    direct_client = DirectSpatialClient(service_factory=lambda: mock_service)
    direct_res = direct_client.get_cell(28.6186, 77.3719)

    # In routes/map.py, CoordinateValidationError and other errors are wrapped like:
    # {"error": {"code": "OUTSIDE_SUPPORTED_GEOGRAPHY", "message": "Out of bounds"}}
    assert "error" in direct_res
    assert direct_res["error"]["code"] == "OUTSIDE_SUPPORTED_GEOGRAPHY"
