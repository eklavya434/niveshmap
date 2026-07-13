"""Unit tests for Nivesh Profile financial capacity and strategy suitability engines."""

import pytest
from src.ncr_intelligence.modeling.suitability import (
    NiveshProfile,
    FinancialCapacityEngine,
    StrategySuitabilityEngine,
    LocationStrategyMatcher,
    load_suitability_config
)

def test_config_loads_properly():
    config = load_suitability_config()
    assert "capacity" in config
    assert "scoring_weights" in config
    assert "location_matching" in config

def test_nivesh_profile_invalid_inputs_rejected():
    # Negative capital rejected
    with pytest.raises(ValueError):
        NiveshProfile({
            "occupation": "SALARIED_PRIVATE",
            "annual_household_income": 1200000.0,
            "available_investment_capital": -500000.0,
            "existing_monthly_emi": 20000.0,
            "number_dependents": 2,
            "current_home_ownership": "OWNS_HOME",
            "investment_horizon": "5_TO_10_YEARS",
            "risk_tolerance": "MODERATE",
            "liquidity_requirement": "LOW",
            "primary_real_estate_goal": "LONG_TERM_APPRECIATION"
        })

    # Invalid dependents rejected
    with pytest.raises(ValueError):
        NiveshProfile({
            "occupation": "SALARIED_PRIVATE",
            "annual_household_income": 1200000.0,
            "available_investment_capital": 500000.0,
            "existing_monthly_emi": 20000.0,
            "number_dependents": -1,
            "current_home_ownership": "OWNS_HOME",
            "investment_horizon": "5_TO_10_YEARS",
            "risk_tolerance": "MODERATE",
            "liquidity_requirement": "LOW",
            "primary_real_estate_goal": "LONG_TERM_APPRECIATION"
        })

def test_zero_income_handled_safely():
    profile = NiveshProfile({
        "occupation": "RETIRED",
        "annual_household_income": 0.0,
        "available_investment_capital": 5000000.0,
        "existing_monthly_emi": 10000.0,
        "number_dependents": 0,
        "current_home_ownership": "OWNS_HOME",
        "investment_horizon": "5_TO_10_YEARS",
        "risk_tolerance": "LOW",
        "liquidity_requirement": "HIGH",
        "primary_real_estate_goal": "RENTAL_INCOME"
    })
    
    engine = FinancialCapacityEngine()
    capacity = engine.evaluate(profile)
    
    assert capacity["monthly_income"] == 0.0
    assert capacity["debt_burden_ratio"] == 1.0 # high ratio because income is zero
    assert capacity["debt_burden"] == "HIGH"

def test_capacity_classification_and_debt_burden():
    # Strong capital with low debt
    profile = NiveshProfile({
        "occupation": "BUSINESS_OWNER",
        "annual_household_income": 3600000.0,
        "available_investment_capital": 20000000.0,
        "existing_monthly_emi": 20000.0, # 20k / 300k = 0.067 (Low)
        "number_dependents": 2,
        "current_home_ownership": "FAMILY_HOME_OR_OTHER",
        "investment_horizon": "MORE_THAN_10_YEARS",
        "risk_tolerance": "HIGH",
        "liquidity_requirement": "LOW",
        "primary_real_estate_goal": "LONG_TERM_APPRECIATION"
    })
    
    engine = FinancialCapacityEngine()
    capacity = engine.evaluate(profile)
    
    assert capacity["debt_burden"] == "LOW"
    assert capacity["capacity_class"] == "VERY_STRONG" # Upgraded from Strong due to low debt burden

def test_strategy_scoring_determinism_and_bounds():
    profile = NiveshProfile({
        "occupation": "SALARIED_PRIVATE",
        "annual_household_income": 1200000.0,
        "available_investment_capital": 3000000.0,
        "existing_monthly_emi": 15000.0,
        "number_dependents": 1,
        "current_home_ownership": "DOES_NOT_OWN_HOME",
        "investment_horizon": "5_TO_10_YEARS",
        "risk_tolerance": "MODERATE",
        "liquidity_requirement": "LOW",
        "primary_real_estate_goal": "LONG_TERM_APPRECIATION"
    })
    
    capacity_engine = FinancialCapacityEngine()
    capacity = capacity_engine.evaluate(profile)
    
    suit_engine = StrategySuitabilityEngine()
    scores1 = suit_engine.calculate(profile, capacity)
    scores2 = suit_engine.calculate(profile, capacity)
    
    # Determinism check
    assert scores1 == scores2
    
    # Check allowed bounds 0-100
    for res in scores1:
        assert 0 <= res["suitability_score"] <= 100
        assert res["suitability_band"] in {"LOW", "MODERATE", "HIGH", "VERY_HIGH"}

def test_penalties_and_hard_gates():
    # 1. High liquidity penalizes land appreciation
    profile_liq = NiveshProfile({
        "occupation": "SALARIED_PRIVATE",
        "annual_household_income": 1500000.0,
        "available_investment_capital": 5000000.0,
        "existing_monthly_emi": 20000.0,
        "number_dependents": 1,
        "current_home_ownership": "OWNS_HOME",
        "investment_horizon": "5_TO_10_YEARS",
        "risk_tolerance": "HIGH",
        "liquidity_requirement": "HIGH",
        "primary_real_estate_goal": "LONG_TERM_APPRECIATION"
    })
    capacity = FinancialCapacityEngine().evaluate(profile_liq)
    scores = StrategySuitabilityEngine().calculate(profile_liq, capacity)
    land_app = next(s for s in scores if s["strategy"] == "LAND_APPRECIATION")
    assert any("liquidity" in factor.lower() for factor in land_app["negative_factors"])

    # 2. Short horizon penalizes land appreciation
    profile_hor = NiveshProfile({
        "occupation": "SALARIED_PRIVATE",
        "annual_household_income": 1500000.0,
        "available_investment_capital": 5000000.0,
        "existing_monthly_emi": 20000.0,
        "number_dependents": 1,
        "current_home_ownership": "OWNS_HOME",
        "investment_horizon": "LESS_THAN_3_YEARS",
        "risk_tolerance": "HIGH",
        "liquidity_requirement": "LOW",
        "primary_real_estate_goal": "LONG_TERM_APPRECIATION"
    })
    capacity = FinancialCapacityEngine().evaluate(profile_hor)
    scores = StrategySuitabilityEngine().calculate(profile_hor, capacity)
    land_app = next(s for s in scores if s["strategy"] == "LAND_APPRECIATION")
    assert any("horizon" in factor.lower() for factor in land_app["negative_factors"])

def test_goal_alignment_and_wait_accumulate_ranking():
    # Low capital profile where WAIT_AND_ACCUMULATE_CAPITAL should rank first
    profile = NiveshProfile({
        "occupation": "FREELANCER",
        "annual_household_income": 400000.0,
        "available_investment_capital": 200000.0,
        "existing_monthly_emi": 10000.0,
        "number_dependents": 3,
        "current_home_ownership": "DOES_NOT_OWN_HOME",
        "investment_horizon": "LESS_THAN_3_YEARS",
        "risk_tolerance": "LOW",
        "liquidity_requirement": "HIGH",
        "primary_real_estate_goal": "BUY_HOME_TO_LIVE"
    })
    capacity = FinancialCapacityEngine().evaluate(profile)
    scores = StrategySuitabilityEngine().calculate(profile, capacity)
    
    assert scores[0]["strategy"] == "WAIT_AND_ACCUMULATE_CAPITAL"

def test_location_strategy_matching_and_insufficient_data():
    matcher = LocationStrategyMatcher()
    
    # Locality lacks baseline metrics -> INSUFFICIENT_DATA
    match = matcher.match_locality(
        strategy="LAND_APPRECIATION",
        locality_meta={"locality_id": "TEST_LOC", "locality_name": "Test Locality", "region": "Noida"},
        readiness_row=None,
        latest_row=None
    )
    assert match["match_band"] == "INSUFFICIENT_DATA"
    assert match["match_score"] == 0

    # Low data readiness -> INSUFFICIENT_DATA
    match = matcher.match_locality(
        strategy="LAND_APPRECIATION",
        locality_meta={"locality_id": "TEST_LOC", "locality_name": "Test Locality", "region": "Noida"},
        readiness_row={"data_readiness_score": 15.0, "readiness_class": "UNSUPPORTED"},
        latest_row={"price_proxy": 5000.0}
    )
    assert match["match_band"] == "INSUFFICIENT_DATA"
    assert match["match_score"] == 0
