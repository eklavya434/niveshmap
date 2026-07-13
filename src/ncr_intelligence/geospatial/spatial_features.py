import geopandas as gpd
from shapely.geometry import Point
from typing import List, Tuple, Dict, Any
from .distances import haversine_distance

class NCRGeospatialProcessor:
    """Geospatial processor utilizing GeoPandas and Shapely to compute transit proximities and buffers."""
    
    def __init__(self):
        pass
        
    def to_gdf(self, coordinates: List[Tuple[float, float]]) -> gpd.GeoDataFrame:
        """
        Converts a list of (latitude, longitude) coordinate tuples into a WGS84 GeoDataFrame.
        Note: Point takes (longitude, latitude) as (x, y) coordinates.
        """
        geometry = [Point(lon, lat) for lat, lon in coordinates]
        gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")
        return gdf

    def get_nearest_distance(self, centroid: Tuple[float, float], targets: List[Tuple[float, float]]) -> float:
        """
        Calculates the Haversine distance in km from a centroid coordinate (lat, lon) 
        to the nearest target coordinate in the targets list.
        """
        if not targets:
            return 999.9  # Fallback large value indicating no targets
            
        min_dist = float('inf')
        for target in targets:
            dist = haversine_distance(centroid[0], centroid[1], target[0], target[1])
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def count_within_radius(
        self, 
        centroid: Tuple[float, float], 
        targets: List[Tuple[float, float]], 
        radius_km: float
    ) -> int:
        """
        Counts how many target coordinates lie within the specified buffer radius (in km) 
        from the locality centroid.
        """
        count = 0
        for target in targets:
            dist = haversine_distance(centroid[0], centroid[1], target[0], target[1])
            if dist <= radius_km:
                count += 1
        return count

    def generate_locality_spatial_features(
        self, 
        centroid: Tuple[float, float], 
        transit_infrastructure_coords: Dict[str, List[Tuple[float, float]]]
    ) -> Dict[str, Any]:
        """
        Computes proximity features for a candidate locality.
        
        Parameters:
        - centroid: (lat, lon) tuple of the locality.
        - transit_infrastructure_coords: Dict mapping key groups ('operational_metro', 'proposed_metro', 
          'expressway', 'airport', 'rrts') to a list of (lat, lon) coordinate tuples.
        """
        features = {}
        
        # Distances to nearest projects
        features["distance_nearest_operational_metro_km"] = self.get_nearest_distance(
            centroid, transit_infrastructure_coords.get("operational_metro", [])
        )
        features["distance_nearest_proposed_metro_km"] = self.get_nearest_distance(
            centroid, transit_infrastructure_coords.get("proposed_metro", [])
        )
        features["distance_nearest_expressway_km"] = self.get_nearest_distance(
            centroid, transit_infrastructure_coords.get("expressway", [])
        )
        features["distance_airport_km"] = self.get_nearest_distance(
            centroid, transit_infrastructure_coords.get("airport", [])
        )
        features["distance_rrts_station_km"] = self.get_nearest_distance(
            centroid, transit_infrastructure_coords.get("rrts", [])
        )
        
        # Proximity counts within buffers
        # Merge all active/operational coordinates for count metrics
        all_operational = (
            transit_infrastructure_coords.get("operational_metro", []) + 
            transit_infrastructure_coords.get("expressway", []) +
            transit_infrastructure_coords.get("rrts", [])
        )
        
        features["infra_count_3km"] = self.count_within_radius(centroid, all_operational, 3.0)
        features["infra_count_5km"] = self.count_within_radius(centroid, all_operational, 5.0)
        features["infra_count_10km"] = self.count_within_radius(centroid, all_operational, 10.0)
        
        return features
