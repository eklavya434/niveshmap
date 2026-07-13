"""Build and persist the locality-coverage H3 grid without creating price estimates.

Run the baseline locality pipeline first so ``localities`` exists, then run:
    $env:PYTHONPATH="."
    python scripts/build_spatial_layer.py
"""

from src.ncr_intelligence.database.connection import Base, engine, get_db_session
from src.ncr_intelligence.database.models import Locality, SpatialCell, SpatialGeometrySource
from src.ncr_intelligence.geospatial.spatial_intelligence import SpatialIntelligenceService


def build_spatial_layer() -> int:
    # In SQLite this creates portable WKT tables. In PostgreSQL, apply the
    # versioned PostGIS migration first; do not rely on create_all for production.
    Base.metadata.create_all(bind=engine)
    service = SpatialIntelligenceService()
    session = get_db_session()
    try:
        required_locality_ids = {locality["locality_id"] for locality in service.localities}
        present_locality_ids = {
            locality_id for (locality_id,) in session.query(Locality.locality_id)
        }
        missing = required_locality_ids - present_locality_ids
        if missing:
            raise RuntimeError(
                "Locality records are missing. Run scripts/build_phase0_dataset.py before building cells. "
                f"Missing: {', '.join(sorted(missing))}"
            )

        source = SpatialGeometrySource(
            source_id="niveshmap_phase0_locality_registry",
            source_name=service.config.source_name,
            source_reference=service.config.source_reference,
            retrieval_date=service.config.retrieval_date,
            license_notes=service.config.license_notes,
            geometry_strategy="LOCALITY_CENTROID_BUFFER",
            notes="Coverage buffers are not locality polygons and use nearest-centroid assignment only.",
        )
        session.merge(source)

        cells = service.generate_supported_cells()
        for cell in cells:
            existing = session.get(SpatialCell, cell.cell_id)
            values = {
                "h3_index": cell.h3_index,
                "h3_resolution": cell.h3_resolution,
                "geometry": cell.geometry.wkt,
                "centroid": cell.centroid.wkt,
                "geometry_srid": cell.geometry_srid,
                "centroid_srid": cell.centroid_srid,
                "centroid_latitude": cell.centroid.y,
                "centroid_longitude": cell.centroid.x,
                "locality_id": cell.assignment.locality_id,
                "region": cell.assignment.region,
                "state_or_ut": cell.assignment.state_or_ut,
                "coverage_status": cell.coverage_status,
                "coordinate_source_id": "niveshmap_phase0_locality_registry",
                "assignment_method": cell.assignment.assignment_method,
                "assignment_distance_km": cell.assignment.assignment_distance_km,
                "assignment_quality_class": cell.assignment.assignment_quality_class,
            }
            if existing is None:
                session.add(SpatialCell(cell_id=cell.cell_id, **values))
            else:
                for key, value in values.items():
                    setattr(existing, key, value)
        session.commit()
        return len(cells)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    count = build_spatial_layer()
    print(f"Persisted {count} supported H3 spatial cells.")
