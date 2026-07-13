import os
import pytest
import pandas as pd
import numpy as np
from datetime import date
from src.ncr_intelligence.modeling.preprocess import encode_stages, split_data_temporally
from src.ncr_intelligence.modeling.models import ForecasterModel, rolling_origin_validation
from src.ncr_intelligence.modeling.forecaster import ScenarioForecaster

def test_stage_encoding():
    df = pd.DataFrame({
        "metro_stage": ["PROPOSED", "UNDER_CONSTRUCTION", "OPERATIONAL", "NONE"],
        "expressway_stage": ["APPROVED", "APPROVED", "APPROVED", "APPROVED"],
        "airport_stage": ["NONE", "NONE", "NONE", "NONE"],
        "rrts_stage": ["NONE", "NONE", "NONE", "NONE"]
    })
    encoded = encode_stages(df)
    
    assert encoded["metro_stage_val"].iloc[0] == 1 # PROPOSED
    assert encoded["metro_stage_val"].iloc[1] == 4 # UNDER_CONSTRUCTION
    assert encoded["metro_stage_val"].iloc[2] == 5 # OPERATIONAL
    assert encoded["metro_stage_val"].iloc[3] == 0 # NONE


def test_temporal_splitting():
    df = pd.DataFrame({
        "quarter": ["2023-Q3", "2023-Q4", "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]
    })
    train, test = split_data_temporally(df, split_quarter="2024-Q2")
    
    # Train set should contain quarters on/before 2024-Q2
    assert max(train["quarter"]) <= "2024-Q2"
    # Test set should contain quarters strictly after 2024-Q2
    assert min(test["quarter"]) > "2024-Q2"
    assert len(train) == 4
    assert len(test) == 2


def test_model_training_and_serialization(tmp_path):
    X = pd.DataFrame({
        "ncr_baseline_index": [100.0, 102.0, 104.0, 106.0, 108.0],
        "distance_nearest_operational_metro_km": [1.5, 1.5, 1.5, 1.5, 1.5],
        "distance_nearest_proposed_metro_km": [4.5, 4.5, 4.5, 4.5, 4.5],
        "distance_nearest_expressway_km": [2.0, 2.0, 2.0, 2.0, 2.0],
        "distance_airport_km": [25.0, 25.0, 25.0, 25.0, 25.0],
        "distance_rrts_station_km": [999.0, 999.0, 999.0, 999.0, 999.0],
        "infra_count_3km": [1, 1, 1, 1, 1],
        "infra_count_5km": [2, 2, 2, 2, 2],
        "infra_count_10km": [4, 4, 4, 4, 4],
        "rera_project_count": [4, 4, 4, 4, 4],
        "metro_stage_val": [5, 5, 5, 5, 5],
        "expressway_stage_val": [5, 5, 5, 5, 5],
        "airport_stage_val": [4, 4, 4, 4, 4],
        "rrts_stage_val": [0, 0, 0, 0, 0]
    })
    y = pd.Series([5000.0, 5100.0, 5200.0, 5300.0, 5400.0])
    
    model = ForecasterModel()
    model.train(X, y)
    
    # Check predictions
    preds = model.predict(X)
    assert len(preds) == 5
    assert preds[0] > 0.0
    
    # Check metrics
    metrics = model.evaluate(X, y)
    assert "mae" in metrics
    assert "mape" in metrics
    
    # Save and reload model
    save_file = os.path.join(tmp_path, "test_model.pickle")
    model.save(save_file)
    assert os.path.exists(save_file)
    
    reloaded = ForecasterModel.load(save_file)
    reloaded_preds = reloaded.predict(X)
    assert np.allclose(preds, reloaded_preds)


def test_scenario_forecaster_simulation():
    # Mock localities metadata
    localities_meta = [{
        "locality_id": "GNW_SEC4",
        "locality_name": "Sector 4 Greater Noida West",
        "region": "Greater Noida West",
        "state_or_ut": "Uttar Pradesh",
        "district": "Gautam Buddha Nagar",
        "latitude": 28.5996,
        "longitude": 77.4497,
        "urban_maturity_class": "EMERGING"
    }]
    
    # Train a dummy model
    X = pd.DataFrame(np.random.rand(10, 14), columns=[
        "ncr_baseline_index", "distance_nearest_operational_metro_km", 
        "distance_nearest_proposed_metro_km", "distance_nearest_expressway_km", 
        "distance_airport_km", "distance_rrts_station_km", "infra_count_3km", 
        "infra_count_5km", "infra_count_10km", "rera_project_count", 
        "metro_stage_val", "expressway_stage_val", "airport_stage_val", "rrts_stage_val"
    ])
    y = pd.Series(np.random.rand(10) * 1000 + 4000)
    
    model = ForecasterModel()
    model.train(X, y)
    
    forecaster = ScenarioForecaster(model, localities_meta)
    
    # Simulate Scenario A (Metro operational) -> distance nearest operational metro should be small (~0.0 km)
    spatial_a = forecaster.simulate_spatial_features(
        locality_id="GNW_SEC4",
        metro_stage="OPERATIONAL",
        expressway_stage="OPERATIONAL",
        airport_stage="APPROVED",
        rrts_stage="NONE"
    )
    assert spatial_a["distance_nearest_operational_metro_km"] == 0.0
    
    # Simulate Scenario B (Metro proposed/none) -> distance operational metro should be larger (fallback/station distance)
    spatial_b = forecaster.simulate_spatial_features(
        locality_id="GNW_SEC4",
        metro_stage="PROPOSED",
        expressway_stage="OPERATIONAL",
        airport_stage="APPROVED",
        rrts_stage="NONE"
    )
    # The nearest operational station is not the local proposed one, so it must be > 0.0
    assert spatial_b["distance_nearest_operational_metro_km"] > 0.0
    assert spatial_b["distance_nearest_proposed_metro_km"] == 0.0 # because it is proposed locally
