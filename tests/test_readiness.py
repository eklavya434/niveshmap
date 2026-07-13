import pytest
from src.ncr_intelligence.quality.readiness import ReadinessScorer

@pytest.fixture
def base_metrics():
    return {
        "locality_id": "NOI_SEC150",
        "price_quarters_count": 28,
        "price_source_quality_avg": 90.0,
        "missing_quarter_pct": 5.0,
        "has_price_provenance": True,
        "infra_reconstructable_events_count": 5,
        "infra_evidence_strength_avg": 0.85,
        "has_geospatial_coordinates": True,
        "has_geospatial_distances": True,
        "analogue_candidates_count": 3,
        "has_socioeconomic_data": True
    }

def test_full_forecast_eligible(base_metrics):
    scorer = ReadinessScorer()
    res = scorer.score_locality(base_metrics)
    
    assert res["readiness_class"] == "FULL_FORECAST_ELIGIBLE"
    assert res["overall_readiness_score"] >= 75.0
    assert res["failure_reasons"] is None


def test_limited_forecast_eligible(base_metrics):
    # Lower observation quarters, increase missingness, and reduce quality signals
    metrics = base_metrics.copy()
    metrics["price_quarters_count"] = 15
    metrics["missing_quarter_pct"] = 30.0
    metrics["price_source_quality_avg"] = 60.0
    metrics["infra_evidence_strength_avg"] = 0.60
    metrics["has_socioeconomic_data"] = False
    
    scorer = ReadinessScorer()
    res = scorer.score_locality(metrics)
    
    assert res["readiness_class"] == "LIMITED_FORECAST_ELIGIBLE"
    assert res["overall_readiness_score"] < 75.0
    assert res["failure_reasons"] is None


def test_gate_failure_missing_provenance(base_metrics):
    # Set price provenance to False
    metrics = base_metrics.copy()
    metrics["has_price_provenance"] = False
    
    scorer = ReadinessScorer()
    res = scorer.score_locality(metrics)
    
    # Missing price provenance fails hard gate, degrades to INTELLIGENCE_ONLY since infra is operational
    assert res["readiness_class"] == "INTELLIGENCE_ONLY"
    assert "provenance" in res["failure_reasons"]


def test_gate_failure_insufficient_price_depth(base_metrics):
    # Price observations count is 5 (minimum is 12)
    metrics = base_metrics.copy()
    metrics["price_quarters_count"] = 5
    
    scorer = ReadinessScorer()
    res = scorer.score_locality(metrics)
    
    assert res["readiness_class"] == "INTELLIGENCE_ONLY"
    assert "price observation depth" in res["failure_reasons"]


def test_gate_failure_no_infra(base_metrics):
    # No infrastructure events
    metrics = base_metrics.copy()
    metrics["infra_reconstructable_events_count"] = 0
    
    scorer = ReadinessScorer()
    res = scorer.score_locality(metrics)
    
    # If no price history or no infra reconstruction, degrades to INTELLIGENCE_ONLY or INSUFFICIENT
    # Since it has price data but fails infra, it is INTELLIGENCE_ONLY (failed infra requirements)
    assert res["readiness_class"] == "INTELLIGENCE_ONLY"
    assert "reconstruction" in res["failure_reasons"]


def test_insufficient_coverage_all_failed():
    metrics = {
        "locality_id": "DEL_UNKNOWN",
        "price_quarters_count": 2,
        "price_source_quality_avg": 20.0,
        "missing_quarter_pct": 90.0,
        "has_price_provenance": False,
        "infra_reconstructable_events_count": 0,
        "infra_evidence_strength_avg": 0.0,
        "has_geospatial_coordinates": False,
        "has_geospatial_distances": False,
        "analogue_candidates_count": 0,
        "has_socioeconomic_data": False
    }
    
    scorer = ReadinessScorer()
    res = scorer.score_locality(metrics)
    
    assert res["readiness_class"] == "INSUFFICIENT_COVERAGE"
    assert res["overall_readiness_score"] < 30.0
    assert len(res["failure_reasons"].split("; ")) >= 3
