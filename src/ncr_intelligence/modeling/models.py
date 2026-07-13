import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit

class ForecasterModel:
    """Wrapper class for scikit-learn RandomForestRegressor model training, evaluation, and serialization."""
    
    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators, 
            random_state=random_state,
            max_depth=8,
            min_samples_split=4
        )
        self.feature_names: List[str] = []

    def train(self, X: pd.DataFrame, y: pd.Series):
        """Trains the random forest regressor model."""
        self.feature_names = list(X.columns)
        self.model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates predictions using the trained model features list."""
        return self.model.predict(X[self.feature_names])

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Calculates evaluation metrics (MAE, RMSE, MAPE)."""
        preds = self.predict(X)
        mae = mean_absolute_error(y, preds)
        rmse = np.sqrt(mean_squared_error(y, preds))
        # Handle zero division defensively
        mape = np.mean(np.abs((y - preds) / np.maximum(y, 1.0))) * 100
        return {
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2),
            "mape": round(float(mape), 2)
        }

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns feature importances mapped to their feature names."""
        importances = self.model.feature_feature_importances_ if hasattr(self.model, "feature_feature_importances_") else self.model.feature_importances_
        return {name: round(float(imp), 4) for name, imp in zip(self.feature_names, importances)}

    def save(self, filepath: str):
        """Serializes and saves the model class using pickle."""
        os_dir = os.path.dirname(filepath)
        if os_dir:
            os.makedirs(os_dir, exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(filepath: str) -> "ForecasterModel":
        """Loads and deserializes a saved ForecasterModel from disk."""
        with open(filepath, "rb") as f:
            return pickle.load(f)


def rolling_origin_validation(
    df: pd.DataFrame, 
    features: List[str], 
    target: str, 
    n_splits: int = 3
) -> List[Dict[str, float]]:
    """
    Performs rolling-origin temporal validation. 
    Splits the data sequentially by quarters to prevent leakage.
    """
    # Sort sequentially by quarter to maintain temporal ordering
    df_sorted = df.sort_values("quarter").reset_index(drop=True)
    
    # We group by quarter to prevent splitting rows within the same quarter across train/test boundary
    unique_quarters = sorted(df_sorted["quarter"].unique())
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    fold_metrics = []
    
    for fold, (train_q_idx, test_q_idx) in enumerate(tscv.split(unique_quarters)):
        train_quarters = [unique_quarters[i] for i in train_q_idx]
        test_quarters = [unique_quarters[i] for i in test_q_idx]
        
        train_fold = df_sorted[df_sorted["quarter"].isin(train_quarters)]
        test_fold = df_sorted[df_sorted["quarter"].isin(test_quarters)]
        
        X_train, y_train = train_fold[features], train_fold[target]
        X_test, y_test = test_fold[features], test_fold[target]
        
        # Train fold model
        fold_model = ForecasterModel()
        fold_model.train(X_train, y_train)
        
        # Evaluate on test fold
        metrics = fold_model.evaluate(X_test, y_test)
        metrics["fold"] = fold + 1
        metrics["train_quarters"] = len(train_quarters)
        metrics["test_quarters"] = len(test_quarters)
        fold_metrics.append(metrics)
        
    return fold_metrics
import os
