"""API error models and spatial exception mapping."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ..geospatial.spatial_intelligence import (
    InvalidSpatialPointError,
    SpatialLayerError,
    UnsupportedGeographyError,
)


class ApiErrorBody(BaseModel):
    code: str
    message: str


class ApiErrorResponse(BaseModel):
    error: ApiErrorBody


def spatial_error_status_code(exc: SpatialLayerError) -> int:
    if isinstance(exc, InvalidSpatialPointError):
        return 400
    if isinstance(exc, UnsupportedGeographyError):
        return 422
    return 500


def spatial_error_payload(exc: SpatialLayerError) -> dict[str, Any]:
    return ApiErrorResponse(
        error=ApiErrorBody(code=exc.code, message=str(exc)),
    ).model_dump()


def internal_spatial_error_payload(message: str = "An internal spatial layer error occurred.") -> dict[str, Any]:
    return ApiErrorResponse(
        error=ApiErrorBody(code="SPATIAL_LAYER_ERROR", message=message),
    ).model_dump()
