"""Spatial-layer tests use explicitly labelled test fixtures, never production data."""

from datetime import date

import pytest
from shapely.geometry import LineString, Point
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.ncr_intelligence.database.connection import Base
from src.ncr_intelligence.database.models import SpatialCell
from src.ncr_intelligence.geospatial.spatial_intelligence import (
    CellInfrastructureFeaturePipeline,
    InfrastructureAsset,
    InvalidSpatialPointError,
    LocalityPriceSignal,
    SpatialConfig,
    SpatialIntelligenceService,
    UnsupportedGeographyError,
    assign_locality_by_centroid,
)


TEST_LOCALITIES = [{
    "locality_id": "TEST_NOIDA",
    "locality_name": "Synthetic Test Locality",
    "region": "Noida",
    "state_or_ut": "Uttar Pradesh",
    "latitude": 28.6186,
    "longitude": 77.3719,
}]


@pytest.fixture
def spatial_config():
    return SpatialConfig(
        h3_resolution=7,
        support_buffer_km=3.0,
        source_name="Synthetic test fixture",
        source_reference="tests/test_spatial_intelligence.py",
        retrieval_date=date(2026, 7, 13),
        license_notes="Test only",
        assignment_max_distance_km=4.0,
    )


@pytest.fixture
def service(spatial_config):
    return SpatialIntelligenceService(localities=TEST_LOCALITIES, config=spatial_config)


def operational_event(event_date=date(2024, 1, 1), publish_date=date(2024, 1, 2)):
    return [{"stage": "OPERATIONAL", "event_date": event_date, "article_publish_date": publish_date}]


def test_valid_point_resolves_to_deterministic_h3_cell(service):
    first = service.cell_for_click(28.6186, 77.3719)
    second = service.cell_for_click(28.6186, 77.3719)

    assert first.h3_index == second.h3_index
    assert first.h3_resolution == 7


def test_invalid_latitude_is_rejected(service):
    with pytest.raises(InvalidSpatialPointError, match="latitude"):
        service.get_cell(91, 77.3719)


def test_invalid_longitude_is_rejected(service):
    with pytest.raises(InvalidSpatialPointError, match="longitude"):
        service.get_cell(28.6186, 181)


def test_outside_supported_geography_is_rejected(service):
    with pytest.raises(UnsupportedGeographyError):
        service.get_cell(28.0, 77.3719)


def test_h3_cell_polygon_is_valid_and_has_wgs84_srid(service):
    cell = service.cell_for_click(28.6186, 77.3719)

    assert cell.geometry.is_valid
    assert cell.geometry.geom_type == "Polygon"
    assert cell.geometry_srid == 4326
    assert cell.centroid_srid == 4326


def test_cell_assignment_preserves_centroid_fallback_and_unassigned_state(service):
    cell = service.cell_for_click(28.6186, 77.3719)
    unassigned = assign_locality_by_centroid(Point(0, 0), TEST_LOCALITIES, max_distance_km=4.0)

    assert cell.assignment.assignment_method == "NEAREST_CENTROID_FALLBACK"
    assert cell.assignment.assignment_distance_km is not None
    assert unassigned.assignment_method == "UNASSIGNED"
    assert unassigned.locality_id is None


def test_future_operational_metro_is_not_visible_in_historical_quarter():
    asset = InfrastructureAsset(
        project_id="TEST_METRO",
        project_type="METRO",
        geometry=Point(77.3719, 28.6186),
        stage_events=operational_event(),
        geometry_available_date=date(2023, 12, 1),
        geometry_role="STATION_POINT",
    )
    pipeline = CellInfrastructureFeaturePipeline([asset])

    assert pipeline.build(Point(77.3719, 28.6186), "2023-Q4")["nearest_operational_metro_km"] is None
    assert pipeline.build(Point(77.3719, 28.6186), "2024-Q1")["nearest_operational_metro_km"] == 0.0


def test_proposed_infrastructure_is_not_visible_before_public_availability_date():
    asset = InfrastructureAsset(
        project_id="TEST_PROPOSAL",
        project_type="METRO",
        geometry=Point(77.3719, 28.6186),
        stage_events=[{
            "stage": "PROPOSED",
            "event_date": date(2019, 12, 1),
            "article_publish_date": date(2020, 4, 2),
        }],
        geometry_available_date=date(2020, 4, 2),
        geometry_role="STATION_POINT",
    )
    pipeline = CellInfrastructureFeaturePipeline([asset])

    assert pipeline.build(Point(77.3719, 28.6186), "2020-Q1")["nearest_proposed_metro_km"] is None
    assert pipeline.build(Point(77.3719, 28.6186), "2020-Q2")["nearest_proposed_metro_km"] == 0.0


def test_expressway_distance_uses_corridor_geometry_not_a_project_centroid():
    # A corridor touches the cell point but its midpoint is kilometres away. A
    # point-centroid implementation would fail this zero-distance assertion.
    asset = InfrastructureAsset(
        project_id="TEST_CORRIDOR",
        project_type="EXPRESSWAY_HIGHWAY",
        geometry=LineString([(77.3719, 28.6186), (77.55, 28.30)]),
        stage_events=operational_event(),
        geometry_role="CORRIDOR_LINE",
    )
    pipeline = CellInfrastructureFeaturePipeline([asset])

    result = pipeline.build(Point(77.3719, 28.6186), "2024-Q1")
    assert result["nearest_expressway_highway_km"] == 0.0


def test_missing_or_invalid_infrastructure_geometry_is_explicitly_unavailable():
    asset = InfrastructureAsset(
        project_id="MISSING_GEOMETRY",
        project_type="METRO",
        geometry=None,
        stage_events=operational_event(),
    )
    result = CellInfrastructureFeaturePipeline([asset]).build(Point(77.3719, 28.6186), "2024-Q1")

    assert result["nearest_operational_metro_km"] is None
    assert result["feature_statuses"]["nearest_operational_metro_km"] == "UNAVAILABLE"
    assert any("MISSING_GEOMETRY" in message for message in result["unavailable_features"])


def test_unverified_price_signal_fails_hard_gate_and_does_not_make_cell_price(service):
    unverified = LocalityPriceSignal(
        locality_id="TEST_NOIDA",
        quarter="2025-Q4",
        price_signal_type="COMPOSITE_PRICE_PROXY",
        value=9999.0,
        verified_for_spatial_serving=False,
        source_reference="tests only",
    )
    guarded = SpatialIntelligenceService(
        localities=TEST_LOCALITIES, config=service.config, price_signals=[unverified]
    )
    response = guarded.get_cell(28.6186, 77.3719, "2025-Q4")

    assert response["price_intelligence"]["estimate_type"] == "SPATIAL_ESTIMATE_NOT_AVAILABLE"
    assert response["price_intelligence"]["value"] is None


def test_verified_locality_signal_preserves_signal_type_without_fabricating_cell_adjustment(service):
    approved = LocalityPriceSignal(
        locality_id="TEST_NOIDA",
        quarter="2025-Q4",
        price_signal_type="CIRCLE_RATE",
        value=8000.0,
        verified_for_spatial_serving=True,
        source_reference="explicit test fixture",
    )
    guarded = SpatialIntelligenceService(
        localities=TEST_LOCALITIES, config=service.config, price_signals=[approved]
    )
    response = guarded.get_cell(28.6186, 77.3719, "2025-Q4")

    assert response["price_intelligence"]["estimate_type"] == "LOCALITY_LEVEL_ESTIMATE_ONLY"
    assert response["price_intelligence"]["price_signal_type"] == "CIRCLE_RATE"
    assert response["data_quality"]["spatial_readiness"] == "LOCALITY_ANCHORED_ONLY"


def test_synthetic_price_data_cannot_enter_spatial_estimate_by_default(service):
    synthetic = LocalityPriceSignal(
        locality_id="TEST_NOIDA",
        quarter="2025-Q4",
        price_signal_type="COMPOSITE_PRICE_PROXY",
        value=7000.0,
        verified_for_spatial_serving=True,
        is_synthetic=True,
        source_reference="synthetic test fixture",
    )
    guarded = SpatialIntelligenceService(
        localities=TEST_LOCALITIES, config=service.config, price_signals=[synthetic]
    )
    response = guarded.get_cell(28.6186, 77.3719, "2025-Q4")

    assert response["price_intelligence"]["estimate_type"] == "SPATIAL_ESTIMATE_NOT_AVAILABLE"
    assert response["price_intelligence"]["value"] is None


def test_estimate_type_is_always_returned(service):
    response = service.get_cell(28.6186, 77.3719, "2025-Q4")

    assert response["price_intelligence"]["estimate_type"] in {
        "SPATIAL_ESTIMATE_NOT_AVAILABLE", "LOCALITY_LEVEL_ESTIMATE_ONLY"
    }


def test_viewport_query_returns_only_cells_with_centroids_inside_requested_bounds(service):
    response = service.get_cells(28.60, 77.35, 28.64, 77.40, "2025-Q4")

    for item in response["cells"]:
        centroid = item["cell"]["centroid"]
        assert 28.60 <= centroid["latitude"] <= 28.64
        assert 77.35 <= centroid["longitude"] <= 77.40


def test_duplicate_h3_cells_are_rejected_by_database_constraint():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        for cell_id in ("872830828ffffff", "872830828fffffe"):
            session.add(SpatialCell(
                cell_id=cell_id,
                h3_index="872830828ffffff",
                h3_resolution=7,
                geometry="POLYGON EMPTY",
                centroid="POINT (77.37 28.62)",
                centroid_latitude=28.62,
                centroid_longitude=77.37,
                coverage_status="TEST",
                assignment_method="UNASSIGNED",
                assignment_quality_class="UNASSIGNED",
            ))
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.close()


def test_scenario_adapter_preserves_locality_model_scope(service):
    response = service.get_cell(28.6186, 77.3719, "2025-Q4", scenario="baseline")

    assert response["scenario"]["scenario_scope"] == "LOCALITY_MODEL_WITH_SPATIAL_CONTEXT"
    assert response["scenario"]["status"] == "NOT_EVALUATED"
