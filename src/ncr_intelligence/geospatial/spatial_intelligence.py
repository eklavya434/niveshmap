"""Defensible H3-based spatial intelligence primitives for NiveshMap.

This module deliberately separates a spatial cell from a parcel and keeps
price-serving conservative.  The current project has locality centroids and
Phase-0 synthetic feasibility outputs, not verified locality polygons,
transaction-level parcels, or production infrastructure geometries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

import h3
import yaml
from pyproj import Transformer
from shapely.geometry import Point, Polygon, box, mapping
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union

from ..features.infrastructure_features import get_project_stage_at_quarter, parse_quarter_to_date
from .distances import haversine_distance


PRICE_ESTIMATE_TYPES = {
    "PARCEL_VERIFIED",
    "CELL_MODEL_ESTIMATE",
    "LOCALITY_ANCHORED_CELL_ESTIMATE",
    "LOCALITY_LEVEL_ESTIMATE_ONLY",
    "PRICE_SIGNAL_ONLY",
    "SPATIAL_ESTIMATE_NOT_AVAILABLE",
}

SPATIAL_READINESS_CLASSES = {
    "FULL_SPATIAL_ESTIMATE",
    "LOCALITY_ANCHORED_ONLY",
    "INFRASTRUCTURE_INTELLIGENCE_ONLY",
    "UNSUPPORTED",
}

ASSIGNMENT_METHODS = {
    "POLYGON_CONTAINMENT",
    "MAJORITY_OVERLAP",
    "NEAREST_CENTROID_FALLBACK",
    "UNASSIGNED",
}

_TO_METRIC = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True).transform
_TO_WGS84 = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True).transform
_PROPOSED_STAGES = {"PROPOSED", "APPROVED", "CONTRACTED", "UNDER_CONSTRUCTION"}


class SpatialLayerError(ValueError):
    """A predictable error suitable for an HTTP adapter to turn into a 4xx response."""

    code = "SPATIAL_LAYER_ERROR"


class InvalidSpatialPointError(SpatialLayerError):
    code = "INVALID_COORDINATES"


class UnsupportedGeographyError(SpatialLayerError):
    code = "OUTSIDE_SUPPORTED_GEOGRAPHY"


@dataclass(frozen=True)
class SpatialConfig:
    h3_resolution: int
    support_buffer_km: float
    source_name: str
    source_reference: str
    retrieval_date: date
    license_notes: str
    assignment_max_distance_km: float
    feature_version: str = "spatial-v1"
    viewport_result_limit: int = 500
    allow_spatial_price_adjustment: bool = False


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_spatial_config(path: Optional[Path] = None) -> SpatialConfig:
    """Load the single source of truth for H3 spatial configuration."""
    config_path = path or project_root() / "config" / "spatial.yaml"
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    supported = raw["supported_area"]
    assignment = raw["cell_locality_assignment"]
    features = raw.get("features", {})
    api = raw.get("api", {})
    return SpatialConfig(
        h3_resolution=int(raw["h3"]["resolution"]),
        support_buffer_km=float(supported["buffer_km"]),
        source_name=str(supported["source_name"]),
        source_reference=str(supported["source_reference"]),
        retrieval_date=date.fromisoformat(str(supported["retrieval_date"])),
        license_notes=str(supported["license_notes"]),
        assignment_max_distance_km=float(assignment["max_assignment_distance_km"]),
        feature_version=str(features.get("version", "spatial-v1")),
        viewport_result_limit=int(api.get("viewport_result_limit", 500)),
        allow_spatial_price_adjustment=bool(features.get("allow_spatial_price_adjustment", False)),
    )


def load_locality_registry(path: Optional[Path] = None) -> list[dict[str, Any]]:
    registry_path = path or project_root() / "config" / "localities.yaml"
    with registry_path.open("r", encoding="utf-8") as handle:
        return list(yaml.safe_load(handle) or [])


def _normalize_locality(locality: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "locality_id": str(locality["locality_id"]),
        "name": str(locality.get("locality_name", locality.get("name", locality["locality_id"]))),
        "region": str(locality["region"]),
        "state_or_ut": str(locality["state_or_ut"]),
        "latitude": float(locality["latitude"]),
        "longitude": float(locality["longitude"]),
    }


def build_supported_area(localities: Sequence[Mapping[str, Any]], buffer_km: float) -> BaseGeometry:
    """Build a documented *coverage* area, never a claimed locality boundary.

    Candidate locality centroids are transformed to UTM 43N for metre-accurate
    buffering, then returned in WGS84.  This is appropriate for the NCR extent.
    """
    if buffer_km <= 0:
        raise ValueError("support buffer must be positive")
    buffers = []
    for raw in localities:
        locality = _normalize_locality(raw)
        centroid = Point(locality["longitude"], locality["latitude"])
        buffers.append(transform(_TO_WGS84, transform(_TO_METRIC, centroid).buffer(buffer_km * 1000)))
    if not buffers:
        raise ValueError("at least one locality centroid is required for spatial coverage")
    return unary_union(buffers)


def _cell_polygon(h3_index: str) -> Polygon:
    boundary = h3.cell_to_boundary(h3_index)
    # H3 returns (lat, lng); Shapely expects (x=lng, y=lat).
    polygon = Polygon([(lng, lat) for lat, lng in boundary])
    if not polygon.is_valid:
        raise SpatialLayerError(f"H3 returned invalid geometry for cell {h3_index}")
    return polygon


@dataclass(frozen=True)
class CellAssignment:
    locality_id: Optional[str]
    locality_name: Optional[str]
    region: Optional[str]
    state_or_ut: Optional[str]
    assignment_method: str
    assignment_distance_km: Optional[float]
    assignment_quality_class: str


def assign_locality_by_centroid(
    point: Point,
    localities: Sequence[Mapping[str, Any]],
    max_distance_km: float,
) -> CellAssignment:
    """Use the documented centroid fallback only when a locality polygon is absent."""
    candidates = []
    for raw in localities:
        locality = _normalize_locality(raw)
        distance = haversine_distance(
            point.y, point.x, locality["latitude"], locality["longitude"]
        )
        candidates.append((distance, locality))
    if not candidates:
        return CellAssignment(None, None, None, None, "UNASSIGNED", None, "UNASSIGNED")

    distance, locality = min(candidates, key=lambda candidate: candidate[0])
    if distance > max_distance_km:
        return CellAssignment(None, None, None, None, "UNASSIGNED", None, "UNASSIGNED")
    return CellAssignment(
        locality_id=locality["locality_id"],
        locality_name=locality["name"],
        region=locality["region"],
        state_or_ut=locality["state_or_ut"],
        assignment_method="NEAREST_CENTROID_FALLBACK",
        assignment_distance_km=distance,
        assignment_quality_class="NEAREST_CENTROID_FALLBACK",
    )


@dataclass(frozen=True)
class SpatialCellContext:
    cell_id: str
    h3_index: str
    h3_resolution: int
    geometry: Polygon
    centroid: Point
    assignment: CellAssignment
    coverage_status: str = "SUPPORTED"
    geometry_srid: int = 4326
    centroid_srid: int = 4326

    def geojson(self) -> dict[str, Any]:
        return mapping(self.geometry)


@dataclass(frozen=True)
class InfrastructureAsset:
    """A geometry with its documented availability and project event history.

    The layer intentionally has no default assets.  Existing coordinate lists in
    Phase-0 scripts are explicitly mock fixtures and must not be promoted here.
    """

    project_id: str
    project_type: str
    geometry: Optional[BaseGeometry]
    stage_events: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    geometry_available_date: Optional[date] = None
    geometry_quality_class: str = "HIGH"
    geometry_role: str = "UNKNOWN"
    source_reference: Optional[str] = None


def _distance_km(point: Point, geometry: BaseGeometry) -> float:
    metric_point = transform(_TO_METRIC, point)
    metric_geometry = transform(_TO_METRIC, geometry)
    return round(metric_point.distance(metric_geometry) / 1000.0, 3)


def _available_status(statuses: Iterable[str]) -> str:
    statuses = list(statuses)
    if not statuses:
        return "UNAVAILABLE"
    if any(status == "LOW_QUALITY_PROXY" for status in statuses):
        return "LOW_QUALITY_PROXY"
    return "AVAILABLE"


class CellInfrastructureFeaturePipeline:
    """Calculate temporal, geometry-aware cell features without leakage."""

    metric_names = (
        "nearest_operational_metro_km",
        "nearest_proposed_metro_km",
        "nearest_rrts_km",
        "nearest_expressway_highway_km",
        "airport_distance_km",
        "metro_count_3km",
        "metro_count_5km",
        "rrts_count_5km",
        "infra_count_3km",
        "infra_count_5km",
        "infra_count_10km",
        "active_project_count",
        "proposed_project_count",
        "under_construction_project_count",
        "operational_project_count",
    )

    def __init__(self, assets: Sequence[InfrastructureAsset] = (), feature_version: str = "spatial-v1"):
        self.assets = list(assets)
        self.feature_version = feature_version

    @staticmethod
    def _asset_is_public(asset: InfrastructureAsset, quarter: str) -> bool:
        as_of = parse_quarter_to_date(quarter)
        return asset.geometry_available_date is None or asset.geometry_available_date <= as_of

    @staticmethod
    def _valid_geometry(asset: InfrastructureAsset) -> bool:
        return asset.geometry is not None and not asset.geometry.is_empty and asset.geometry.is_valid

    @staticmethod
    def _semantic_geometry_is_valid(asset: InfrastructureAsset) -> bool:
        if not CellInfrastructureFeaturePipeline._valid_geometry(asset):
            return False
        geom_type = asset.geometry.geom_type
        if asset.project_type == "METRO":
            return geom_type == "Point"
        if asset.project_type == "EXPRESSWAY_HIGHWAY":
            # A single project centroid is not a corridor-distance substitute.
            return geom_type in {"LineString", "MultiLineString"}
        if asset.project_type == "AIRPORT":
            return geom_type in {"Point", "Polygon", "MultiPolygon"}
        if asset.project_type == "RRTS":
            return geom_type in {"Point", "LineString", "MultiLineString"}
        return False

    def build(self, point: Point, quarter: str) -> dict[str, Any]:
        # Validates the caller's requested as-of quarter before examining assets.
        parse_quarter_to_date(quarter)
        values: dict[str, Any] = {name: None for name in self.metric_names}
        statuses = {name: "UNAVAILABLE" for name in self.metric_names}
        unavailable: list[str] = []
        usable: list[tuple[InfrastructureAsset, str, float]] = []

        for asset in self.assets:
            if not self._asset_is_public(asset, quarter):
                continue
            stage = get_project_stage_at_quarter(list(asset.stage_events), quarter)
            if stage is None:
                continue
            if not self._semantic_geometry_is_valid(asset):
                unavailable.append(f"{asset.project_id}: geometry unavailable or invalid for {asset.project_type} distance semantics")
                continue
            usable.append((asset, stage, _distance_km(point, asset.geometry)))

        def distances(project_type: str, predicate) -> list[tuple[InfrastructureAsset, float]]:
            return [(asset, distance) for asset, stage, distance in usable if asset.project_type == project_type and predicate(stage)]

        operational_metros = distances("METRO", lambda stage: stage == "OPERATIONAL")
        proposed_metros = distances("METRO", lambda stage: stage in _PROPOSED_STAGES)
        rrts = distances("RRTS", lambda stage: stage == "OPERATIONAL")
        expressways = distances("EXPRESSWAY_HIGHWAY", lambda stage: stage == "OPERATIONAL")
        airports = distances("AIRPORT", lambda stage: stage in _PROPOSED_STAGES | {"OPERATIONAL"})

        def set_distance(metric: str, rows: list[tuple[InfrastructureAsset, float]]) -> None:
            if rows:
                values[metric] = min(distance for _, distance in rows)
                statuses[metric] = _available_status(asset.geometry_quality_class for asset, _ in rows)

        set_distance("nearest_operational_metro_km", operational_metros)
        set_distance("nearest_proposed_metro_km", proposed_metros)
        set_distance("nearest_rrts_km", rrts)
        set_distance("nearest_expressway_highway_km", expressways)
        set_distance("airport_distance_km", airports)

        metro_rows = operational_metros + proposed_metros
        if metro_rows:
            for radius in (3, 5):
                metric = f"metro_count_{radius}km"
                values[metric] = sum(distance <= radius for _, distance in metro_rows)
                statuses[metric] = _available_status(asset.geometry_quality_class for asset, _ in metro_rows)
        if rrts:
            values["rrts_count_5km"] = sum(distance <= 5 for _, distance in rrts)
            statuses["rrts_count_5km"] = _available_status(asset.geometry_quality_class for asset, _ in rrts)
        if usable:
            for radius in (3, 5, 10):
                metric = f"infra_count_{radius}km"
                values[metric] = sum(distance <= radius for _, _, distance in usable)
                statuses[metric] = _available_status(asset.geometry_quality_class for asset, _, _ in usable)
            stages = [stage for _, stage, _ in usable]
            values["active_project_count"] = sum(stage != "STALLED_DELAYED_CANCELLED" for stage in stages)
            values["proposed_project_count"] = sum(stage in {"PROPOSED", "APPROVED", "CONTRACTED"} for stage in stages)
            values["under_construction_project_count"] = sum(stage == "UNDER_CONSTRUCTION" for stage in stages)
            values["operational_project_count"] = sum(stage == "OPERATIONAL" for stage in stages)
            for metric in ("active_project_count", "proposed_project_count", "under_construction_project_count", "operational_project_count"):
                statuses[metric] = _available_status(asset.geometry_quality_class for asset, _, _ in usable)

        return {
            **values,
            "feature_version": self.feature_version,
            "feature_statuses": statuses,
            "unavailable_features": sorted(set(unavailable)),
        }


@dataclass(frozen=True)
class LocalityPriceSignal:
    locality_id: str
    quarter: str
    price_signal_type: str
    value: Optional[float]
    unit: str = "INR_PER_SQFT"
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    verified_for_spatial_serving: bool = False
    is_synthetic: bool = False
    source_reference: Optional[str] = None


class SpatialReadinessEvaluator:
    """Categorical gates; it intentionally does not invent a new 0-100 score."""

    def assess(
        self,
        cell: SpatialCellContext,
        price_signal: Optional[LocalityPriceSignal],
        infrastructure: Mapping[str, Any],
    ) -> dict[str, Any]:
        price_ready = bool(
            price_signal
            and price_signal.value is not None
            and price_signal.verified_for_spatial_serving
            and not price_signal.is_synthetic
        )
        geometry_ready = any(
            status in {"AVAILABLE", "LOW_QUALITY_PROXY"}
            for status in infrastructure["feature_statuses"].values()
        )
        if cell.assignment.locality_id is None:
            readiness = "UNSUPPORTED"
        elif price_ready:
            # The configured layer does not permit an unvalidated spatial price adjustment.
            readiness = "LOCALITY_ANCHORED_ONLY"
        elif geometry_ready:
            readiness = "INFRASTRUCTURE_INTELLIGENCE_ONLY"
        else:
            readiness = "UNSUPPORTED"
        return {
            "spatial_readiness": readiness,
            "locality_assignment_quality": cell.assignment.assignment_quality_class,
            "coordinate_completeness": "COMPLETE",
            "locality_price_readiness": "READY" if price_ready else "NOT_READY",
            "infrastructure_geometry_quality": "READY" if geometry_ready else "NOT_READY",
            "temporal_spatial_feature_completeness": "READY" if geometry_ready else "NOT_READY",
            "spatial_adjustment_support": "NOT_SUPPORTED",
        }


class SpatialIntelligenceService:
    """Map-ready use-case service for click analysis and viewport cells.

    A future HTTP adapter can expose ``get_cell`` as ``GET /api/map/cell`` and
    ``get_cells`` as ``GET /api/map/cells`` without changing this domain logic.
    """

    def __init__(
        self,
        localities: Optional[Sequence[Mapping[str, Any]]] = None,
        config: Optional[SpatialConfig] = None,
        infrastructure_assets: Sequence[InfrastructureAsset] = (),
        price_signals: Sequence[LocalityPriceSignal] = (),
    ):
        self.config = config or load_spatial_config()
        self.localities = [_normalize_locality(item) for item in (localities or load_locality_registry())]
        self.supported_area = build_supported_area(self.localities, self.config.support_buffer_km)
        self.pipeline = CellInfrastructureFeaturePipeline(infrastructure_assets, self.config.feature_version)
        self.readiness = SpatialReadinessEvaluator()
        self.price_signals = list(price_signals)
        self._cells: dict[str, SpatialCellContext] = {}

    @staticmethod
    def _default_quarter() -> str:
        """Current calendar quarter when no latest verified data resolver exists."""
        today = date.today()
        return f"{today.year}-Q{((today.month - 1) // 3) + 1}"

    def _validate_point(self, latitude: float, longitude: float) -> Point:
        try:
            latitude, longitude = float(latitude), float(longitude)
        except (TypeError, ValueError) as exc:
            raise InvalidSpatialPointError("latitude and longitude must be numeric") from exc
        if not -90 <= latitude <= 90:
            raise InvalidSpatialPointError("latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise InvalidSpatialPointError("longitude must be between -180 and 180")
        point = Point(longitude, latitude)
        if not self.supported_area.covers(point):
            raise UnsupportedGeographyError(
                "Point is outside documented NiveshMap locality-centroid coverage zones."
            )
        return point

    def _make_cell(self, h3_index: str) -> SpatialCellContext:
        polygon = _cell_polygon(h3_index)
        latitude, longitude = h3.cell_to_latlng(h3_index)
        centroid = Point(longitude, latitude)
        assignment = assign_locality_by_centroid(
            centroid, self.localities, self.config.assignment_max_distance_km
        )
        return SpatialCellContext(
            cell_id=h3_index,
            h3_index=h3_index,
            h3_resolution=h3.get_resolution(h3_index),
            geometry=polygon,
            centroid=centroid,
            assignment=assignment,
        )

    def cell_for_click(self, latitude: float, longitude: float) -> SpatialCellContext:
        point = self._validate_point(latitude, longitude)
        h3_index = h3.latlng_to_cell(point.y, point.x, self.config.h3_resolution)
        if h3_index not in self._cells:
            self._cells[h3_index] = self._make_cell(h3_index)
        return self._cells[h3_index]

    def generate_supported_cells(self) -> list[SpatialCellContext]:
        """Generate only cells whose H3 centres fall within documented coverage."""
        for h3_index in h3.geo_to_cells(mapping(self.supported_area), self.config.h3_resolution):
            if h3_index not in self._cells:
                self._cells[h3_index] = self._make_cell(h3_index)
        return [self._cells[index] for index in sorted(self._cells)]

    def _signal_for(self, locality_id: Optional[str], quarter: str) -> Optional[LocalityPriceSignal]:
        if locality_id is None:
            return None
        candidates = [
            signal for signal in self.price_signals
            if signal.locality_id == locality_id and signal.quarter <= quarter
        ]
        return max(candidates, key=lambda signal: signal.quarter) if candidates else None

    @staticmethod
    def _price_response(signal: Optional[LocalityPriceSignal], quarter: str, locality_assigned: bool) -> tuple[dict[str, Any], list[str]]:
        limitations: list[str] = []
        if not locality_assigned:
            limitations.append("No defensible locality assignment exists for this spatial cell.")
        if signal is None:
            limitations.append("No production-verified locality price signal is registered for spatial serving.")
        elif signal.is_synthetic:
            limitations.append("Synthetic or sample price data is blocked from spatial estimate serving.")
        elif not signal.verified_for_spatial_serving:
            limitations.append("Locality price signal has not passed the spatial-serving provenance gate.")
        elif signal.value is None:
            limitations.append("The approved locality price signal contains no numeric value.")

        if limitations:
            return ({
                "estimate_type": "SPATIAL_ESTIMATE_NOT_AVAILABLE",
                "price_signal_type": signal.price_signal_type if signal else None,
                "value": None,
                "lower_bound": None,
                "upper_bound": None,
                "unit": signal.unit if signal else "INR_PER_SQFT",
                "as_of_quarter": signal.quarter if signal else quarter,
            }, limitations)

        # This is deliberately locality-level, never a copied cell prediction.
        return ({
            "estimate_type": "LOCALITY_LEVEL_ESTIMATE_ONLY",
            "price_signal_type": signal.price_signal_type,
            "value": signal.value,
            "lower_bound": signal.lower_bound,
            "upper_bound": signal.upper_bound,
            "unit": signal.unit,
            "as_of_quarter": signal.quarter,
        }, limitations)

    def _scenario_context(self, scenario: Optional[str], cell: SpatialCellContext, infrastructure: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        if scenario is None:
            return None
        if cell.assignment.locality_id is None:
            return {
                "scenario_id": scenario,
                "scenario_scope": "UNAVAILABLE",
                "status": "NOT_EVALUATED",
                "limitation": "Existing scenario forecaster requires a locality ID.",
            }
        return {
            "scenario_id": scenario,
            "scenario_scope": "LOCALITY_MODEL_WITH_SPATIAL_CONTEXT",
            "status": "NOT_EVALUATED",
            "locality_id": cell.assignment.locality_id,
            "spatial_context_feature_version": infrastructure["feature_version"],
            "limitation": "The existing scenario model is locality-trained; no cell-trained scenario adjustment is applied.",
        }

    def _cell_payload(self, cell: SpatialCellContext, quarter: str, scenario: Optional[str] = None) -> dict[str, Any]:
        infrastructure = self.pipeline.build(cell.centroid, quarter)
        signal = self._signal_for(cell.assignment.locality_id, quarter)
        price, limitations = self._price_response(signal, quarter, cell.assignment.locality_id is not None)
        readiness = self.readiness.assess(cell, signal, infrastructure)
        return {
            "cell": {
                "cell_id": cell.cell_id,
                "h3_index": cell.h3_index,
                "resolution": cell.h3_resolution,
                "geometry": cell.geojson(),
                "geometry_srid": cell.geometry_srid,
                "centroid": {"latitude": cell.centroid.y, "longitude": cell.centroid.x},
                "spatial_readiness": readiness["spatial_readiness"],
                "coverage_status": cell.coverage_status,
                "assignment_method": cell.assignment.assignment_method,
                "assignment_distance_km": cell.assignment.assignment_distance_km,
                "assignment_quality_class": cell.assignment.assignment_quality_class,
            },
            "locality": {
                "locality_id": cell.assignment.locality_id,
                "name": cell.assignment.locality_name,
                "region": cell.assignment.region,
                "state_or_ut": cell.assignment.state_or_ut,
            },
            "price_intelligence": price,
            "infrastructure": {
                name: infrastructure[name] for name in self.pipeline.metric_names
            },
            "data_quality": {
                **readiness,
                # Locality Data Readiness is intentionally not copied into a
                # cell readiness score. An adapter may populate this separately
                # from a provenance-approved locality readiness record.
                "locality_data_readiness": None,
                "feature_statuses": infrastructure["feature_statuses"],
                "unavailable_features": infrastructure["unavailable_features"],
                "limitations": limitations + infrastructure["unavailable_features"],
            },
            "scenario": self._scenario_context(scenario, cell, infrastructure),
        }

    def get_cell(self, latitude: float, longitude: float, quarter: Optional[str] = None, scenario: Optional[str] = None) -> dict[str, Any]:
        quarter = quarter or self._default_quarter()
        parse_quarter_to_date(quarter)
        cell = self.cell_for_click(latitude, longitude)
        return {
            "location": {"latitude": float(latitude), "longitude": float(longitude)},
            "as_of_quarter": quarter,
            **self._cell_payload(cell, quarter, scenario),
        }

    def get_cells(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        quarter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        if min_lat > max_lat or min_lon > max_lon:
            raise InvalidSpatialPointError("viewport minimum bounds must not exceed maximum bounds")
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90 and -180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            raise InvalidSpatialPointError("viewport bounds are outside valid WGS84 coordinate ranges")
        quarter = quarter or self._default_quarter()
        parse_quarter_to_date(quarter)
        viewport = box(min_lon, min_lat, max_lon, max_lat)
        result_limit = min(limit or self.config.viewport_result_limit, self.config.viewport_result_limit)
        cells = [
            cell for cell in self.generate_supported_cells()
            if viewport.covers(cell.centroid)
        ][:result_limit]
        return {
            "as_of_quarter": quarter,
            "viewport": {"min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon},
            "result_limit": result_limit,
            "returned_cells": len(cells),
            "cells": [self._cell_payload(cell, quarter) for cell in cells],
        }
