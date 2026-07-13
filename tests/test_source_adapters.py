import os
import pytest
from datetime import date
from src.ncr_intelligence.ingestion.nhb import NHBResidexAdapter
from src.ncr_intelligence.ingestion.rera.up_rera import UPRERAAdapter
from src.ncr_intelligence.ingestion.rera.hrera import HRERAAdapter
from src.ncr_intelligence.ingestion.rera.delhi_rera import DelhiRERAAdapter
from src.ncr_intelligence.ingestion.circle_rates.up import UPCircleRatesAdapter
from src.ncr_intelligence.ingestion.circle_rates.haryana import HaryanaCollectorRatesAdapter
from src.ncr_intelligence.ingestion.circle_rates.delhi import DelhiCircleRatesAdapter
from src.ncr_intelligence.ingestion.infrastructure.pib import PIBAdapter
from src.ncr_intelligence.ingestion.infrastructure.authorities import TransitAuthoritiesAdapter

# Test RERA Adapters
def test_up_rera_adapter():
    filepath = "data/sample/up_rera.json"
    assert os.path.exists(filepath)
    
    adapter = UPRERAAdapter({"source_id": "up_rera"})
    records = adapter.parse_projects(filepath)
    
    assert len(records) == 2
    assert records[0]["reg_no"] == "PRJ12345"
    
    norm = adapter.normalize_project(records[0])
    assert norm["project_id"] == "UP_PRJ12345"
    assert norm["price_value"] == 6500.0
    assert norm["price_unit"] == "INR/sqft"


def test_hrera_adapter():
    filepath = "data/sample/hrera.json"
    assert os.path.exists(filepath)
    
    adapter = HRERAAdapter({"source_id": "hrera_gurugram"})
    records = adapter.parse_projects(filepath)
    
    assert len(records) == 2
    norm = adapter.normalize_project(records[0])
    assert norm["project_id"] == "HR_HR-GG-2018-05"
    assert norm["price_value"] == 7200.0


def test_delhi_rera_adapter():
    filepath = "data/sample/delhi_rera.json"
    assert os.path.exists(filepath)
    
    adapter = DelhiRERAAdapter({"source_id": "delhi_rera"})
    records = adapter.parse_projects(filepath)
    
    assert len(records) == 2
    norm = adapter.normalize_project(records[1])
    assert norm["project_id"] == "DEL_DLRERA2019P0020"
    # Price per sqm is 95000, divided by 10.7639 ~= 8825.8
    assert norm["price_value"] == 8825.8


# Test Circle Rate Adapters
def test_up_circle_rates_adapter():
    filepath = "data/sample/up_circle_rates.csv"
    assert os.path.exists(filepath)
    
    adapter = UPCircleRatesAdapter({"source_id": "up_circle_rates"})
    records = adapter.parse_rates(filepath)
    
    assert len(records) >= 3
    rate = adapter.get_rate_for_locality(records, "NOI_SEC150")
    assert rate["circle_rate"] == 5600.0


def test_haryana_collector_rates_adapter():
    filepath = "data/sample/haryana_collector_rates.csv"
    assert os.path.exists(filepath)
    
    adapter = HaryanaCollectorRatesAdapter({"source_id": "haryana_collector_rates"})
    records = adapter.parse_rates(filepath)
    
    rate = adapter.get_rate_for_locality(records, "GUR_DLF3")
    assert rate["collector_rate"] == 7500.0


def test_delhi_circle_rates_adapter():
    filepath = "data/sample/delhi_circle_rates.csv"
    assert os.path.exists(filepath)
    
    adapter = DelhiCircleRatesAdapter({"source_id": "delhi_circle_rates"})
    records = adapter.parse_rates(filepath)
    
    # DLF VK SEC A is Category A -> 7200
    rate_vk = adapter.get_rate_for_locality(records, "DEL_VK_SEC_A")
    assert rate_vk["circle_rate"] == 7200.0
    
    # Dwarka Sector 10 is Category H -> 1500
    rate_dwr = adapter.get_rate_for_locality(records, "DEL_DWR_SEC10")
    assert rate_dwr["circle_rate"] == 1500.0


# Test NHB Residex Adapter
def test_nhb_residex_adapter():
    filepath = "data/sample/nhb_residex.csv"
    assert os.path.exists(filepath)
    
    adapter = NHBResidexAdapter({"source_id": "nhb_residex"})
    records = adapter.parse_index(filepath)
    
    assert len(records) == 15
    assert records[0]["quarter"] == "2019-Q1"
    assert records[0]["city"] == "Delhi"
    assert records[0]["index_value"] == 100.0


# Test PIB and Transit Events
def test_pib_adapter():
    filepath = "data/sample/pib_approvals.json"
    assert os.path.exists(filepath)
    
    adapter = PIBAdapter({"source_id": "pib_news"})
    records = adapter.parse_events(filepath)
    
    assert len(records) == 2
    assert records[0]["project_name"] == "Noida International Airport Jewar"
    assert records[0]["stage"] == "APPROVED"
    assert records[0]["event_date"] == date(2018, 5, 10)


def test_transit_authorities_adapter():
    filepath = "data/sample/transit_events.json"
    assert os.path.exists(filepath)
    
    adapter = TransitAuthoritiesAdapter({"source_id": "dmrc_metro"})
    records = adapter.parse_events(filepath)
    
    assert len(records) == 2
    assert records[0]["project_id"] == "dmrc_blue_ext"
    assert records[0]["stage"] == "OPERATIONAL"
    assert records[0]["event_date"] == date(2019, 3, 9)
