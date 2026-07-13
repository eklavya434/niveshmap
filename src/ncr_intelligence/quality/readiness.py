import os
import yaml
from typing import Dict, Any, List, Tuple

def load_readiness_config() -> Dict[str, Any]:
    """Loads readiness configuration from config/data_readiness.yaml."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    config_path = os.path.join(base_dir, "config", "data_readiness.yaml")
    
    if not os.path.exists(config_path):
        # Fallback defaults matching configuration requirements
        return {
            "weights": {
                "historical_price_coverage": 0.20,
                "price_source_quality": 0.15,
                "quarterly_observation_depth": 0.15,
                "infrastructure_event_history": 0.15,
                "infrastructure_evidence_coverage": 0.10,
                "geospatial_completeness": 0.10,
                "historical_analogue_depth": 0.05,
                "socioeconomic_feature_completeness": 0.10
            },
            "thresholds": {
                "min_quarters_full_forecast": 20,
                "preferred_quarters_full_forecast": 28,
                "max_missing_quarter_pct_full_forecast": 20.0,
                "min_quarters_limited_forecast": 12,
                "min_infra_reconstructable_events": 1,
                "min_readiness_score_full": 75.0,
                "min_readiness_score_limited": 50.0,
                "min_readiness_score_intel_only": 30.0
            },
            "hard_gates": {
                "require_price_provenance": True,
                "min_price_observations_count": 12,
                "require_temporal_infra_reconstruction": True
            }
        }
        
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class ReadinessScorer:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_readiness_config()
        self.weights = self.config["weights"]
        self.thresholds = self.config["thresholds"]
        self.hard_gates = self.config["hard_gates"]

    def calculate_dimension_scores(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Calculates dimension scores out of 100 based on raw locality metrics."""
        scores = {}
        
        # 1. Historical Price Coverage: relative to preferred quarters
        pref_quarters = self.thresholds.get("preferred_quarters_full_forecast", 28)
        price_quarters = metrics.get("price_quarters_count", 0)
        scores["historical_price_coverage"] = min(100.0, (price_quarters / pref_quarters) * 100.0)
        
        # 2. Price Source Quality: directly 0-100 score
        scores["price_source_quality"] = float(metrics.get("price_source_quality_avg", 0.0))
        
        # 3. Quarterly Observation Depth: based on missing quarter percentage
        missing_pct = metrics.get("missing_quarter_pct", 100.0)
        scores["quarterly_observation_depth"] = max(0.0, 100.0 - missing_pct)
        
        # 4. Infrastructure Event History: relative to representative event timeline depth (e.g. 5 stages)
        infra_events = metrics.get("infra_reconstructable_events_count", 0)
        scores["infrastructure_event_history"] = min(100.0, (infra_events / 5.0) * 100.0)
        
        # 5. Infrastructure Evidence Coverage: average confidence (0.0 to 1.0) * 100
        scores["infrastructure_evidence_coverage"] = float(metrics.get("infra_evidence_strength_avg", 0.0) * 100.0)
        
        # 6. Geospatial Completeness: binary indicator for coordinates and distances
        has_coords = metrics.get("has_geospatial_coordinates", False)
        has_dist = metrics.get("has_geospatial_distances", False)
        scores["geospatial_completeness"] = 100.0 if (has_coords and has_dist) else 0.0
        
        # 7. Historical Analogue Depth: binary indicator if we have analogue candidates
        analogues = metrics.get("analogue_candidates_count", 0)
        scores["historical_analogue_depth"] = min(100.0, analogues * 50.0)
        
        # 8. Socioeconomic Feature Completeness: binary indicator for urban maturity etc.
        has_socio = metrics.get("has_socioeconomic_data", False)
        scores["socioeconomic_feature_completeness"] = 100.0 if has_socio else 0.0
        
        return scores

    def evaluate_hard_gates(self, metrics: Dict[str, Any]) -> List[str]:
        """Evaluates minimum analytical gates and returns lists of failed requirements."""
        failures = []
        
        # Price Provenance Gate
        if self.hard_gates.get("require_price_provenance", True):
            if not metrics.get("has_price_provenance", False):
                failures.append("Missing price source provenance (provenance verification failed)")
                
        # Price Observations Depth Gate
        min_price_count = self.hard_gates.get("min_price_observations_count", 12)
        if metrics.get("price_quarters_count", 0) < min_price_count:
            failures.append(f"Insufficient price observation depth (found {metrics.get('price_quarters_count', 0)} of min {min_price_count} quarters)")
            
        # Infrastructure Reconstruction Gate
        if self.hard_gates.get("require_temporal_infra_reconstruction", True):
            min_infra_events = self.thresholds.get("min_infra_reconstructable_events", 1)
            if metrics.get("infra_reconstructable_events_count", 0) < min_infra_events:
                failures.append("Temporal infrastructure reconstruction impossible (no stage transitions found)")
                
        return failures

    def score_locality(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the readiness framework and determines forecast eligibility class."""
        dimension_scores = self.calculate_dimension_scores(metrics)
        
        # Calculate overall weighted score
        overall_score = 0.0
        for dim, weight in self.weights.items():
            overall_score += dimension_scores.get(dim, 0.0) * weight
            
        # Check hard gates
        failed_gates = self.evaluate_hard_gates(metrics)
        
        # Determine classification and eligibility
        readiness_class = "INSUFFICIENT_COVERAGE"
        forecast_eligibility = "Excluded from forecasting due to failed hard gates."
        
        price_quarters = metrics.get("price_quarters_count", 0)
        missing_pct = metrics.get("missing_quarter_pct", 100.0)
        infra_events = metrics.get("infra_reconstructable_events_count", 0)
        
        if not failed_gates:
            # Gates passed, check score thresholds
            if (overall_score >= self.thresholds["min_readiness_score_full"] and
                price_quarters >= self.thresholds["min_quarters_full_forecast"] and
                missing_pct <= self.thresholds["max_missing_quarter_pct_full_forecast"]):
                readiness_class = "FULL_FORECAST_ELIGIBLE"
                forecast_eligibility = "Eligible for full infrastructure scenario forecasting."
            elif (overall_score >= self.thresholds["min_readiness_score_limited"] and
                  price_quarters >= self.thresholds["min_quarters_limited_forecast"]):
                readiness_class = "LIMITED_FORECAST_ELIGIBLE"
                forecast_eligibility = "Eligible for limited forecasting with wider uncertainty bounds."
            else:
                readiness_class = "INTELLIGENCE_ONLY"
                forecast_eligibility = "Eligible for infrastructure intelligence and historical analogue matching only."
        else:
            # Hard gates failed. Determine if intelligence-only is possible
            has_coords = metrics.get("has_geospatial_coordinates", False)
            has_usable_price = (price_quarters >= self.thresholds.get("min_quarters_limited_forecast", 12) and 
                                metrics.get("has_price_provenance", False))
            has_usable_infra = (infra_events >= self.thresholds.get("min_infra_reconstructable_events", 1))
            
            if has_coords and (has_usable_price or has_usable_infra):
                readiness_class = "INTELLIGENCE_ONLY"
                if not has_usable_price:
                    forecast_eligibility = "Eligible for infrastructure intelligence only (failed price history requirements)."
                else:
                    forecast_eligibility = "Eligible for historical price trends and analogues only (failed infrastructure event requirements)."
            else:
                readiness_class = "INSUFFICIENT_COVERAGE"
                forecast_eligibility = "Insufficient data coverage for analytical use."

        return {
            "locality_id": metrics.get("locality_id"),
            "price_coverage_score": round(dimension_scores["historical_price_coverage"], 2),
            "price_source_quality_score": round(dimension_scores["price_source_quality"], 2),
            "quarterly_observation_score": round(dimension_scores["quarterly_observation_depth"], 2),
            "infrastructure_history_score": round(dimension_scores["infrastructure_event_history"], 2),
            "infrastructure_evidence_score": round(dimension_scores["infrastructure_evidence_coverage"], 2),
            "geospatial_completeness_score": round(dimension_scores["geospatial_completeness"], 2),
            "analogue_depth_score": round(dimension_scores["historical_analogue_depth"], 2),
            "socioeconomic_completeness_score": round(dimension_scores["socioeconomic_feature_completeness"], 2),
            "overall_readiness_score": round(overall_score, 2),
            "readiness_class": readiness_class,
            "forecast_eligibility": forecast_eligibility,
            "failure_reasons": "; ".join(failed_gates) if failed_gates else None
        }
