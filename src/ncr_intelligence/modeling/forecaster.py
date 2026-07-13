import os
import pandas as pd
from typing import Dict, Any, List
from .models import ForecasterModel
from .preprocess import STAGE_MAPPING, FEATURE_COLUMNS
from ..geospatial.spatial_features import NCRGeospatialProcessor

# Import project coordinates from build script for context matching
PROJECT_COORDINATES = {
    "metro_stations": [
        (28.5818, 77.0592), (28.6186, 77.3719), (28.4682, 77.5147),
        (28.4664, 77.5092), (28.4554, 77.4727), (28.5996, 77.4497),
        (28.4907, 77.0984), (28.4721, 77.3168)
    ],
    "expressways": [
        (28.5300, 77.3800), (28.6100, 77.3500), (28.3000, 77.5500),
        (28.4000, 76.9800), (28.4800, 77.0800), (28.4300, 77.3300)
    ],
    "airports": [
        (28.5562, 77.1000), (28.1500, 77.5500)
    ],
    "rrts_stations": [
        (28.7061, 77.4419)
    ]
}

class ScenarioForecaster:
    def __init__(self, model: ForecasterModel, localities_metadata: List[Dict[str, Any]]):
        self.model = model
        self.localities_metadata = {loc["locality_id"]: loc for loc in localities_metadata}
        self.geo_processor = NCRGeospatialProcessor()

    def simulate_spatial_features(
        self, 
        locality_id: str, 
        metro_stage: str, 
        expressway_stage: str, 
        airport_stage: str, 
        rrts_stage: str
    ) -> Dict[str, Any]:
        """Simulates spatial features under a user-defined what-if scenario."""
        loc = self.localities_metadata.get(locality_id)
        if not loc:
            raise ValueError(f"Locality ID {locality_id} not found in registered metadata.")
            
        centroid = (loc["latitude"], loc["longitude"])
        
        # Build coordinates dynamically based on hypothetical stages
        op_metro = []
        prop_metro = []
        for station in PROJECT_COORDINATES["metro_stations"]:
            if station == (28.5996, 77.4497):  # Noida Extension station
                if metro_stage == "OPERATIONAL":
                    op_metro.append(station)
                elif metro_stage != "NONE":
                    prop_metro.append(station)
            else:
                op_metro.append(station)
                
        op_exp = []
        for exp in PROJECT_COORDINATES["expressways"]:
            if exp == (28.4000, 76.9800):  # Dwarka Expressway
                if expressway_stage == "OPERATIONAL":
                    op_exp.append(exp)
            else:
                op_exp.append(exp)
                
        op_airport = [(28.5562, 77.1000)]
        if airport_stage == "OPERATIONAL":
            op_airport.append((28.1500, 77.5500))
            
        op_rrts = []
        if rrts_stage == "OPERATIONAL":
            op_rrts.append((28.7061, 77.4419))
            
        transit_infrastructure_coords = {
            "operational_metro": op_metro,
            "proposed_metro": prop_metro,
            "expressway": op_exp,
            "airport": op_airport,
            "rrts": op_rrts
        }
        
        return self.geo_processor.generate_locality_spatial_features(centroid, transit_infrastructure_coords)

    def forecast_scenario(
        self, 
        locality_id: str, 
        metro_stage: str, 
        expressway_stage: str, 
        airport_stage: str, 
        rrts_stage: str, 
        n_quarters: int = 4,
        latest_row: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates scenario-conditioned price trend forecasts for the next N quarters.
        """
        # Run spatial simulation
        spatial_feats = self.simulate_spatial_features(
            locality_id, metro_stage, expressway_stage, airport_stage, rrts_stage
        )
        
        # Get baseline parameters
        latest_base_index = float(latest_row.get("ncr_baseline_index", 150.0)) if latest_row else 150.0
        latest_price_val = float(latest_row.get("price_proxy", 6000.0)) if latest_row else 6000.0
        
        forecast_results = []
        current_price = latest_price_val
        
        for q in range(1, n_quarters + 1):
            future_qtr = f"2026-Q{q}"
            
            # Predict baseline growth
            future_base_index = latest_base_index * (1.0 + q * 0.018)
            
            # Construct feature row
            row_dict = {
                "ncr_baseline_index": future_base_index,
                "distance_nearest_operational_metro_km": spatial_feats["distance_nearest_operational_metro_km"],
                "distance_nearest_proposed_metro_km": spatial_feats["distance_nearest_proposed_metro_km"],
                "distance_nearest_expressway_km": spatial_feats["distance_nearest_expressway_km"],
                "distance_airport_km": spatial_feats["distance_airport_km"],
                "distance_rrts_station_km": spatial_feats["distance_rrts_station_km"],
                "infra_count_3km": spatial_feats["infra_count_3km"],
                "infra_count_5km": spatial_feats["infra_count_5km"],
                "infra_count_10km": spatial_feats["infra_count_10km"],
                "rera_project_count": int(latest_row.get("rera_project_count", 4)) if latest_row else 4,
                "metro_stage_val": STAGE_MAPPING.get(metro_stage, 0),
                "expressway_stage_val": STAGE_MAPPING.get(expressway_stage, 0),
                "airport_stage_val": STAGE_MAPPING.get(airport_stage, 0),
                "rrts_stage_val": STAGE_MAPPING.get(rrts_stage, 0)
            }
            
            # Convert to DataFrame matching model features order
            X_df = pd.DataFrame([row_dict])
            pred_val = float(self.model.predict(X_df)[0])
            
            # Smooth prediction (adjust relative to last price value to avoid erratic jumps)
            forecast_results.append({
                "quarter": future_qtr,
                "forecasted_price_proxy": round(pred_val, 2),
                "ncr_baseline_index": round(future_base_index, 2),
                "metro_stage": metro_stage,
                "expressway_stage": expressway_stage,
                "airport_stage": airport_stage,
                "rrts_stage": rrts_stage
            })
            
        return forecast_results
