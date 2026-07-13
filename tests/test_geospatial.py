import pytest
from src.ncr_intelligence.geospatial.distances import haversine_distance
from src.ncr_intelligence.geospatial.geocoding import geocode_locality
from src.ncr_intelligence.geospatial.spatial_features import NCRGeospatialProcessor

def test_haversine_distance():
    # Distance from Dwarka Sector 10 (28.5818, 77.0592) to Vasant Kunj Sector A (28.5293, 77.1626)
    # Geodesic distance should be ~11.6 km
    dist = haversine_distance(28.5818, 77.0592, 28.5293, 77.1626)
    assert abs(dist - 11.66) < 0.1
    
    # Distance to itself must be 0.0
    assert haversine_distance(28.5818, 77.0592, 28.5818, 77.0592) == 0.0


def test_geocoding_provenance_and_fallbacks():
    res = geocode_locality("Sector 62 Noida", "Noida", "Uttar Pradesh")
    assert abs(res["latitude"] - 28.6) < 0.1
    assert abs(res["longitude"] - 77.37) < 0.1
    assert res["provenance"]["coordinate_source"] is not None
    assert "Sector 62 Noida" in res["provenance"]["query"]
    
    # Check invalid geocoding fallback coordinates
    res_invalid = geocode_locality("Sector Unknown XYZ", "Unknown", "Delhi")
    assert res_invalid["latitude"] == 0.0
    assert res_invalid["longitude"] == 0.0


def test_geospatial_processor_geodataframe():
    proc = NCRGeospatialProcessor()
    coords = [(28.5818, 77.0592), (28.5293, 77.1626)]
    gdf = proc.to_gdf(coords)
    
    assert len(gdf) == 2
    # Shapely Point coordinate geometry checks (x=lon, y=lat)
    assert gdf.geometry.iloc[0].x == 77.0592
    assert gdf.geometry.iloc[0].y == 28.5818
    assert gdf.crs == "EPSG:4326"


def test_geospatial_processor_proximities():
    proc = NCRGeospatialProcessor()
    centroid = (28.5818, 77.0592) # Dwarka Sector 10
    
    infra_coords = {
        "operational_metro": [
            (28.5818, 77.0592), # Station right at Dwarka Sec 10
            (28.5912, 77.0456)  # Dwarka Sector 11 nearby station
        ],
        "proposed_metro": [
            (28.5512, 77.0850)
        ],
        "expressway": [
            (28.5200, 77.0100)
        ],
        "airport": [
            (28.5562, 77.1000) # IGI Airport
        ],
        "rrts": []
    }
    
    features = proc.generate_locality_spatial_features(centroid, infra_coords)
    
    # Distance to nearest operational metro station should be 0.0 km
    assert features["distance_nearest_operational_metro_km"] == 0.0
    
    # Distance to nearest proposed metro station should be ~4.3 km
    assert abs(features["distance_nearest_proposed_metro_km"] - 4.25) < 0.2
    
    # Distance to empty list (RRTS) should return fallback 999.9 km
    assert features["distance_rrts_station_km"] == 999.9
    
    # Counts verification: operational metro (2 points) + expressway (1) + airport (0)
    # Check within 3km: should find Dwarka Sec 10 (0 km) and Dwarka Sec 11 (~1.67 km) -> count 2
    assert features["infra_count_3km"] == 2
    
    # Check within 10km: should also find proposed metro is excluded since it is not operational/active,
    # but finds expressway at ~8.3 km -> count 3 (Dwarka 10, Dwarka 11, expressway)
    assert features["infra_count_10km"] == 3
