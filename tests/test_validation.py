import pytest
from datetime import date
from pydantic import ValidationError
from src.ncr_intelligence.utils.validation import (
    LocalityValidator, SourceValidator, PriceObservationValidator,
    InfrastructureProjectValidator, InfrastructureEventValidator
)

def test_locality_validation():
    # Valid locality setup
    valid_data = {
        "locality_id": "DEL_DWR_SEC10",
        "name": "Dwarka Sector 10",
        "region": "Delhi",
        "state_or_ut": "Delhi",
        "district": "South West Delhi",
        "latitude": 28.5818,
        "longitude": 77.0592,
        "urban_maturity_class": "MATURE",
        "candidate_exposure_types": ["metro"],
        "candidate_control_group": False,
        "notes": "Test notes"
    }
    loc = LocalityValidator(**valid_data)
    assert loc.locality_id == "DEL_DWR_SEC10"
    assert loc.latitude == 28.5818
    
    # Invalid latitude check (NCR bounds validation)
    invalid_lat = valid_data.copy()
    invalid_lat["latitude"] = 35.5
    with pytest.raises(ValidationError) as excinfo:
        LocalityValidator(**invalid_lat)
    assert "latitude" in str(excinfo.value)

    # Invalid region check
    invalid_region = valid_data.copy()
    invalid_region["region"] = "Mumbai South"
    with pytest.raises(ValidationError) as excinfo:
        LocalityValidator(**invalid_region)
    assert "region" in str(excinfo.value)


def test_source_validation():
    valid_source = {
        "source_id": "up_rera",
        "source_name": "UP RERA",
        "source_category": "rera",
        "geography": "Uttar Pradesh",
        "official_source": True,
        "access_method": "html",
        "expected_format": "html"
    }
    src = SourceValidator(**valid_source)
    assert src.source_id == "up_rera"
    assert src.access_method == "html"
    
    # Invalid access method check
    invalid_access = valid_source.copy()
    invalid_access["access_method"] = "crawler"
    with pytest.raises(ValidationError):
        SourceValidator(**invalid_access)


def test_price_observation_validation():
    valid_obs = {
        "locality_id": "DEL_DWR_SEC10",
        "observation_date": date(2022, 6, 30),
        "quarter": "2022-Q2",
        "price_value": 8500.0,
        "price_unit": "INR/sqft",
        "price_type": "circle_rate",
        "source_id": "delhi_circle_rates",
        "source_quality_class": "HIGH",
        "is_proxy": True
    }
    obs = PriceObservationValidator(**valid_obs)
    assert obs.quarter == "2022-Q2"
    
    # Invalid quarter formatting
    invalid_qtr = valid_obs.copy()
    invalid_qtr["quarter"] = "2022/Q2"
    with pytest.raises(ValidationError):
        PriceObservationValidator(**invalid_qtr)
        
    # Invalid price type
    invalid_type = valid_obs.copy()
    invalid_type["price_type"] = "inflated_rate"
    with pytest.raises(ValidationError):
        PriceObservationValidator(**invalid_type)


def test_infrastructure_project_validation():
    valid_proj = {
        "project_id": "dmrc_blue_line",
        "project_name": "DMRC Blue Line",
        "normalized_name": "dmrc_blue_line",
        "project_type": "METRO",
        "primary_authority": "DMRC",
        "current_stage": "OPERATIONAL"
    }
    proj = InfrastructureProjectValidator(**valid_proj)
    assert proj.project_type == "METRO"
    
    # Invalid stage category
    invalid_stage = valid_proj.copy()
    invalid_stage["current_stage"] = "DRAFT"
    with pytest.raises(ValidationError):
        InfrastructureProjectValidator(**invalid_stage)


def test_infrastructure_event_validation():
    valid_event = {
        "project_id": "dmrc_blue_line",
        "stage": "OPERATIONAL",
        "event_date": date(2005, 12, 31),
        "evidence_source_id": "dmrc_metro",
        "evidence_strength": 0.95
    }
    evt = InfrastructureEventValidator(**valid_event)
    assert evt.evidence_strength == 0.95
    
    # Invalid evidence strength range
    invalid_strength = valid_event.copy()
    invalid_strength["evidence_strength"] = 1.1
    with pytest.raises(ValidationError):
        InfrastructureEventValidator(**invalid_strength)
