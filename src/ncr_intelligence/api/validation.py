"""HTTP-layer coordinate validation before delegating to the spatial service."""

from __future__ import annotations

import math
from typing import Optional


class CoordinateValidationError(ValueError):
    """Predictable coordinate validation failure for HTTP adapters."""

    code = "INVALID_COORDINATES"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _parse_required_float(raw: Optional[str], name: str) -> float:
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        raise CoordinateValidationError(f"{name} is required")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise CoordinateValidationError(f"{name} must be numeric") from exc
    if math.isnan(value):
        raise CoordinateValidationError(f"{name} must not be NaN")
    if math.isinf(value):
        raise CoordinateValidationError(f"{name} must be a finite number")
    return value


def parse_latitude(raw: Optional[str]) -> float:
    value = _parse_required_float(raw, "latitude")
    if not -90 <= value <= 90:
        raise CoordinateValidationError("latitude must be between -90 and 90")
    return value


def parse_longitude(raw: Optional[str]) -> float:
    value = _parse_required_float(raw, "longitude")
    if not -180 <= value <= 180:
        raise CoordinateValidationError("longitude must be between -180 and 180")
    return value


def parse_viewport_bounds(
    min_lat_raw: Optional[str],
    min_lon_raw: Optional[str],
    max_lat_raw: Optional[str],
    max_lon_raw: Optional[str],
) -> tuple[float, float, float, float]:
    for raw, name in (
        (min_lat_raw, "min_lat"),
        (min_lon_raw, "min_lon"),
        (max_lat_raw, "max_lat"),
        (max_lon_raw, "max_lon"),
    ):
        if raw is None or (isinstance(raw, str) and raw.strip() == ""):
            raise CoordinateValidationError(f"{name} is required")

    min_lat = parse_latitude(min_lat_raw)
    min_lon = parse_longitude(min_lon_raw)
    max_lat = parse_latitude(max_lat_raw)
    max_lon = parse_longitude(max_lon_raw)

    if min_lat >= max_lat:
        raise CoordinateValidationError("min_lat must be less than max_lat")
    if min_lon >= max_lon:
        raise CoordinateValidationError("min_lon must be less than max_lon")

    return min_lat, min_lon, max_lat, max_lon
