"""HTTP adapter tests for map spatial endpoints."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.ncr_intelligence.api.app import create_app
from src.ncr_intelligence.api.dependencies import get_spatial_service
from src.ncr_intelligence.api.routes import map as map_routes
from src.ncr_intelligence.geospatial.spatial_intelligence import (
    SpatialConfig,
    SpatialIntelligenceService,
    SpatialLayerError,
    UnsupportedGeographyError,
)

TEST_LOCALITIES = [{
    "locality_id": "TEST_NOIDA",
    "locality_name": "Synthetic Test Locality",
    "region": "Noida",
    "state_or_ut": "Uttar Pradesh",
    "latitude": 28.6186,
    "longitude": 77.3719,
}]


def _sample_cell_payload(*, estimate_type: str = "SPATIAL_ESTIMATE_NOT_AVAILABLE", value=None, readiness="UNSUPPORTED"):
    return {
        "location": {"latitude": 28.6186, "longitude": 77.3719},
        "as_of_quarter": "2025-Q4",
        "cell": {
            "cell_id": "872830828ffffff",
            "h3_index": "872830828ffffff",
            "resolution": 7,
            "geometry": {"type": "Polygon", "coordinates": []},
            "centroid": {"latitude": 28.6186, "longitude": 77.3719},
            "spatial_readiness": readiness,
            "assignment_method": "NEAREST_CENTROID_FALLBACK",
        },
        "locality": {"locality_id": "TEST_NOIDA", "name": "Synthetic Test Locality", "region": "Noida"},
        "price_intelligence": {
            "estimate_type": estimate_type,
            "price_signal_type": None,
            "value": value,
            "lower_bound": None,
            "upper_bound": None,
            "unit": "INR_PER_SQFT",
            "as_of_quarter": "2025-Q4",
        },
        "infrastructure": {"nearest_operational_metro_km": None},
        "data_quality": {
            "spatial_readiness": readiness,
            "limitations": [],
            "feature_statuses": {},
            "unavailable_features": [],
        },
        "scenario": None,
    }


def _sample_cells_payload(*, cells=None):
    if cells is None:
        cells = [_sample_cell_payload()]
    return {
        "as_of_quarter": "2025-Q4",
        "viewport": {"min_lat": 28.60, "min_lon": 77.35, "max_lat": 28.64, "max_lon": 77.40},
        "result_limit": 500,
        "returned_cells": len(cells),
        "cells": cells,
    }


@pytest.fixture
def mock_service():
    service = MagicMock(spec=SpatialIntelligenceService)
    service.get_cell.return_value = _sample_cell_payload()
    service.get_cells.return_value = _sample_cells_payload()
    return service


@pytest.fixture
def client(mock_service):
    app = create_app(service_factory=lambda: mock_service)
    app.dependency_overrides[get_spatial_service] = lambda: mock_service
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client, mock_service
    app.dependency_overrides.clear()


@pytest.fixture
def real_service_client():
    config = SpatialConfig(
        h3_resolution=7,
        support_buffer_km=3.0,
        source_name="Synthetic test fixture",
        source_reference="tests/test_map_api.py",
        retrieval_date=date(2026, 7, 13),
        license_notes="Test only",
        assignment_max_distance_km=4.0,
    )
    service = SpatialIntelligenceService(localities=TEST_LOCALITIES, config=config)
    app = create_app(service_factory=lambda: service)
    app.dependency_overrides[get_spatial_service] = lambda: service
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client, service
    app.dependency_overrides.clear()


class TestGetMapCell:
    def test_valid_coordinates_accepted(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        assert response.status_code == 200
        mock_service.get_cell.assert_called_once_with(28.6186, 77.3719, quarter=None, scenario=None)

    def test_missing_latitude_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lon": "77.3719"})
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_COORDINATES"
        mock_service.get_cell.assert_not_called()

    def test_missing_longitude_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lat": "28.6186"})
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_COORDINATES"
        mock_service.get_cell.assert_not_called()

    def test_latitude_above_90_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lat": "91", "lon": "77.3719"})
        assert response.status_code == 400
        assert "latitude" in response.json()["error"]["message"]
        mock_service.get_cell.assert_not_called()

    def test_latitude_below_minus_90_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lat": "-91", "lon": "77.3719"})
        assert response.status_code == 400
        mock_service.get_cell.assert_not_called()

    def test_longitude_above_180_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "181"})
        assert response.status_code == 400
        mock_service.get_cell.assert_not_called()

    def test_longitude_below_minus_180_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "-181"})
        assert response.status_code == 400
        mock_service.get_cell.assert_not_called()

    def test_nan_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lat": "NaN", "lon": "77.3719"})
        assert response.status_code == 400
        assert "NaN" in response.json()["error"]["message"]
        mock_service.get_cell.assert_not_called()

    def test_infinity_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get("/api/map/cell", params={"lat": "Infinity", "lon": "77.3719"})
        assert response.status_code == 400
        mock_service.get_cell.assert_not_called()

    def test_unsupported_geography_handled_explicitly(self, client):
        test_client, mock_service = client
        mock_service.get_cell.side_effect = UnsupportedGeographyError("outside coverage")
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "OUTSIDE_SUPPORTED_GEOGRAPHY"

    def test_service_get_cell_is_called(self, client):
        test_client, mock_service = client
        test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719", "quarter": "2025-Q4"})
        mock_service.get_cell.assert_called_once_with(28.6186, 77.3719, quarter="2025-Q4", scenario=None)

    def test_service_response_taxonomy_preserved(self, client):
        test_client, _ = client
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        body = response.json()
        assert "cell" in body
        assert "price_intelligence" in body
        assert "data_quality" in body

    def test_estimate_type_preserved(self, client):
        test_client, mock_service = client
        mock_service.get_cell.return_value = _sample_cell_payload(
            estimate_type="LOCALITY_LEVEL_ESTIMATE_ONLY", value=8000.0
        )
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        assert response.json()["price_intelligence"]["estimate_type"] == "LOCALITY_LEVEL_ESTIMATE_ONLY"

    def test_null_price_remains_null(self, client):
        test_client, mock_service = client
        mock_service.get_cell.return_value = _sample_cell_payload()
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        assert response.json()["price_intelligence"]["value"] is None

    def test_infrastructure_intelligence_only_state_remains_non_numeric(self, client):
        test_client, mock_service = client
        mock_service.get_cell.return_value = _sample_cell_payload(readiness="INFRASTRUCTURE_INTELLIGENCE_ONLY")
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        body = response.json()
        assert body["cell"]["spatial_readiness"] == "INFRASTRUCTURE_INTELLIGENCE_ONLY"
        assert body["price_intelligence"]["value"] is None

    def test_service_failure_is_not_returned_as_fake_success(self, client):
        test_client, mock_service = client
        mock_service.get_cell.side_effect = SpatialLayerError("controlled failure")
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "SPATIAL_LAYER_ERROR"

    def test_internal_stack_trace_is_not_exposed(self, client):
        test_client, mock_service = client
        mock_service.get_cell.side_effect = RuntimeError("unexpected boom")
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        assert response.status_code == 500
        assert "Traceback" not in response.text
        assert "unexpected boom" not in response.text


class TestGetMapCells:
    def test_valid_bounding_box_accepted(self, client):
        test_client, mock_service = client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "77.35", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert response.status_code == 200
        mock_service.get_cells.assert_called_once_with(28.60, 77.35, 28.64, 77.40, quarter=None)

    def test_inverted_latitude_bounds_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.64", "min_lon": "77.35", "max_lat": "28.60", "max_lon": "77.40"},
        )
        assert response.status_code == 400
        assert "min_lat" in response.json()["error"]["message"]
        mock_service.get_cells.assert_not_called()

    def test_inverted_longitude_bounds_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "77.40", "max_lat": "28.64", "max_lon": "77.35"},
        )
        assert response.status_code == 400
        assert "min_lon" in response.json()["error"]["message"]
        mock_service.get_cells.assert_not_called()

    def test_invalid_latitude_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "95", "min_lon": "77.35", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert response.status_code == 400
        mock_service.get_cells.assert_not_called()

    def test_invalid_longitude_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "200", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert response.status_code == 400
        mock_service.get_cells.assert_not_called()

    def test_nan_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "NaN", "min_lon": "77.35", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert response.status_code == 400
        mock_service.get_cells.assert_not_called()

    def test_infinity_rejected(self, client):
        test_client, mock_service = client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "Infinity", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert response.status_code == 400
        mock_service.get_cells.assert_not_called()

    def test_service_get_cells_is_called(self, client):
        test_client, mock_service = client
        test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "77.35", "max_lat": "28.64", "max_lon": "77.40", "quarter": "2025-Q4"},
        )
        mock_service.get_cells.assert_called_once_with(28.60, 77.35, 28.64, 77.40, quarter="2025-Q4")

    def test_viewport_cell_states_preserved(self, client):
        test_client, mock_service = client
        mock_service.get_cells.return_value = _sample_cells_payload(
            cells=[_sample_cell_payload(readiness="INFRASTRUCTURE_INTELLIGENCE_ONLY")]
        )
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "77.35", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert response.json()["cells"][0]["cell"]["spatial_readiness"] == "INFRASTRUCTURE_INTELLIGENCE_ONLY"

    def test_null_prices_remain_null(self, client):
        test_client, mock_service = client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "77.35", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert response.json()["cells"][0]["price_intelligence"]["value"] is None

    def test_empty_valid_viewport_distinguished_from_query_failure(self, client):
        test_client, mock_service = client
        mock_service.get_cells.return_value = _sample_cells_payload(cells=[])
        empty_response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "77.35", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert empty_response.status_code == 200
        assert empty_response.json()["returned_cells"] == 0

        mock_service.get_cells.side_effect = SpatialLayerError("database unavailable")
        failure_response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.60", "min_lon": "77.35", "max_lat": "28.64", "max_lon": "77.40"},
        )
        assert failure_response.status_code == 500
        assert failure_response.json()["error"]["code"] == "SPATIAL_LAYER_ERROR"

    def test_route_does_not_independently_calculate_h3_cells(self):
        assert "h3" not in map_routes.__dict__

    def test_route_does_not_fabricate_price_values(self, client):
        test_client, mock_service = client
        mock_service.get_cell.return_value = _sample_cell_payload()
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719"})
        assert response.json()["price_intelligence"]["estimate_type"] == "SPATIAL_ESTIMATE_NOT_AVAILABLE"
        assert response.json()["price_intelligence"]["value"] is None


class TestRealServiceIntegration:
    def test_supported_point_returns_200(self, real_service_client):
        test_client, _ = real_service_client
        response = test_client.get("/api/map/cell", params={"lat": "28.6186", "lon": "77.3719", "quarter": "2025-Q4"})
        assert response.status_code == 200
        assert response.json()["price_intelligence"]["estimate_type"] == "SPATIAL_ESTIMATE_NOT_AVAILABLE"

    def test_outside_coverage_returns_422(self, real_service_client):
        test_client, _ = real_service_client
        response = test_client.get("/api/map/cell", params={"lat": "28.0", "lon": "77.3719"})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "OUTSIDE_SUPPORTED_GEOGRAPHY"

    def test_service_invalid_latitude_still_maps_to_400(self, real_service_client):
        test_client, _ = real_service_client
        response = test_client.get("/api/map/cell", params={"lat": "91", "lon": "77.3719"})
        assert response.status_code == 400

    def test_service_inverted_bounds_still_maps_to_400(self, real_service_client):
        test_client, _ = real_service_client
        response = test_client.get(
            "/api/map/cells",
            params={"min_lat": "28.64", "min_lon": "77.35", "max_lat": "28.60", "max_lon": "77.40"},
        )
        assert response.status_code == 400
