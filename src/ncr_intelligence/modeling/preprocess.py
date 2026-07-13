import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any

# Ordinal stage mapping based on infrastructure_types config
STAGE_MAPPING = {
    "NONE": 0,
    "PROPOSED": 1,
    "APPROVED": 2,
    "CONTRACTED": 3,
    "UNDER_CONSTRUCTION": 4,
    "OPERATIONAL": 5,
    "STALLED_DELAYED_CANCELLED": 6
}

FEATURE_COLUMNS = [
    "ncr_baseline_index",
    "distance_nearest_operational_metro_km",
    "distance_nearest_proposed_metro_km",
    "distance_nearest_expressway_km",
    "distance_airport_km",
    "distance_rrts_station_km",
    "infra_count_3km",
    "infra_count_5km",
    "infra_count_10km",
    "rera_project_count",
    "metro_stage_val",
    "expressway_stage_val",
    "airport_stage_val",
    "rrts_stage_val"
]

def encode_stages(df: pd.DataFrame) -> pd.DataFrame:
    """Encodes infrastructure stage strings into ordinal numeric values."""
    df = df.copy()
    for col in ["metro_stage", "expressway_stage", "airport_stage", "rrts_stage"]:
        val_col = f"{col}_val"
        df[val_col] = df[col].map(STAGE_MAPPING).fillna(0).astype(int)
    return df

def load_and_preprocess_panel(
    panel_csv: str, 
    locality_feasibility_csv: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads panel data and filters out localities that do not meet 
    data readiness requirements for forecasting (forecast eligibility gate).
    """
    panel_df = pd.read_csv(panel_csv)
    feasibility_df = pd.read_csv(locality_feasibility_csv)
    
    # Identify forecast-eligible localities
    eligible_classes = {"FULL_FORECAST_ELIGIBLE", "LIMITED_FORECAST_ELIGIBLE"}
    eligible_locs = set(
        feasibility_df[feasibility_df["readiness_class"].isin(eligible_classes)]["locality_id"]
    )
    
    # Filter panel rows
    filtered_panel = panel_df[panel_df["locality_id"].isin(eligible_locs)].copy()
    
    # Fill remaining missing price proxies with historical backward-fill per locality
    # (Only for cases where minor intermediate quarters are missing)
    filtered_panel["price_proxy"] = filtered_panel.groupby("locality_id")["price_proxy"].ffill().bfill()
    
    # Encode stages ordinally
    processed_df = encode_stages(filtered_panel)
    
    return processed_df, feasibility_df

def split_data_temporally(
    df: pd.DataFrame, 
    split_quarter: str = "2024-Q3"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits the panel dataset into train and test sets based on a quarter boundary 
    to guarantee no leakage of future information.
    """
    train_df = df[df["quarter"] <= split_quarter].copy()
    test_df = df[df["quarter"] > split_quarter].copy()
    return train_df, test_df
