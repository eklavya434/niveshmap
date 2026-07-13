import os
import yaml
from datetime import date
from src.ncr_intelligence.modeling.preprocess import load_and_preprocess_panel, split_data_temporally, FEATURE_COLUMNS
from src.ncr_intelligence.modeling.models import ForecasterModel, rolling_origin_validation
from src.ncr_intelligence.modeling.forecaster import ScenarioForecaster

def load_localities_yaml() -> list:
    yaml_path = "config/localities.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    print("====================================================")
    print("NCR REAL ESTATE: TRAINING FORECASTING ENGINE MODEL")
    print("====================================================")
    
    panel_csv = "data/processed/phase0_quarterly_panel.csv"
    feasibility_csv = "data/processed/locality_feasibility.csv"
    
    if not os.path.exists(panel_csv) or not os.path.exists(feasibility_csv):
        print("Error: Phase 0 datasets not found. Run scripts/build_phase0_dataset.py first.")
        return
        
    # 1. Preprocess panel
    print("Loading and preprocessing quarterly panel data...")
    df, feasibility_df = load_and_preprocess_panel(panel_csv, feasibility_csv)
    
    # 2. Run Rolling-Origin Cross-Validation
    print("Running temporal rolling-origin cross-validation...")
    target = "price_proxy"
    fold_metrics = rolling_origin_validation(df, FEATURE_COLUMNS, target, n_splits=3)
    
    for metrics in fold_metrics:
        print(f"Fold {metrics['fold']}: MAE={metrics['mae']}, RMSE={metrics['rmse']}, MAPE={metrics['mape']}% "
              f"(Train Qtrs: {metrics['train_quarters']}, Test Qtrs: {metrics['test_quarters']})")
              
    # 3. Train final model on all data
    print("Training final model on all forecast-eligible records...")
    X, y = df[FEATURE_COLUMNS], df[target]
    model = ForecasterModel()
    model.train(X, y)
    
    # 4. Print Feature Importances
    importances = model.get_feature_importances()
    print("\nFeature Importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        print(f" - {feat}: {imp}")
        
    # 5. Serialize Model
    model_path = "data/processed/forecaster.pickle"
    model.save(model_path)
    print(f"\nTrained model serialized to: {model_path}")
    
    # 6. Run What-If Scenario Simulation Demo
    localities_metadata = load_localities_yaml()
    forecaster = ScenarioForecaster(model, localities_metadata)
    
    # Get latest row for Noida Extension (GNW_SEC4) to use as simulation baseline
    latest_row = df[df["locality_id"] == "GNW_SEC4"].iloc[-1].to_dict()
    
    print("\n----------------------------------------------------")
    print("WHAT-IF SCENARIO ENGINE DEMO (Noida Extension)")
    print("----------------------------------------------------")
    
    print("\nScenario A: Metro OPERATIONAL, Airport APPROVED")
    fc_a = forecaster.forecast_scenario(
        locality_id="GNW_SEC4",
        metro_stage="OPERATIONAL",
        expressway_stage="OPERATIONAL",
        airport_stage="APPROVED",
        rrts_stage="NONE",
        n_quarters=4,
        latest_row=latest_row
    )
    for row in fc_a:
        print(f" {row['quarter']}: Forecasted Price = {row['forecasted_price_proxy']} INR/sqft")
        
    print("\nScenario B: Metro PROPOSED, Airport APPROVED")
    fc_b = forecaster.forecast_scenario(
        locality_id="GNW_SEC4",
        metro_stage="PROPOSED",
        expressway_stage="OPERATIONAL",
        airport_stage="APPROVED",
        rrts_stage="NONE",
        n_quarters=4,
        latest_row=latest_row
    )
    for row in fc_b:
        print(f" {row['quarter']}: Forecasted Price = {row['forecasted_price_proxy']} INR/sqft")
        
    print("\nModel training and validation execution completed successfully.")

if __name__ == "__main__":
    main()
