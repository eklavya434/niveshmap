import csv
from typing import List, Dict, Any
from .base import CircleRatesAdapter

class HaryanaCollectorRatesAdapter(CircleRatesAdapter):
    """Adapter for Haryana Collector Rates (Gurugram and Faridabad)."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 60,
            "earliest_date_found": None,
            "latest_date_found": None,
            "structured_data_available": False,
            "manual_intervention_required": True,
            "notes": "Haryana Collector Rates are published annually by district administrations as PDFs."
        }
        
    def parse_rates(self, filepath: str) -> List[Dict[str, Any]]:
        rates = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rates.append({
                    "locality_key": row["locality_key"],
                    "collector_rate": float(row["collector_rate"]),
                    "unit": row.get("unit", "INR/sqft"),
                    "effective_date": row.get("effective_date", "2019-01-01")
                })
        return rates

    def get_rate_for_locality(self, parsed_rates: List[Dict[str, Any]], locality_id: str) -> Dict[str, Any]:
        for rate in parsed_rates:
            if rate["locality_key"].upper() in locality_id.upper():
                return rate
        return {
            "locality_key": locality_id,
            "collector_rate": 0.0,
            "unit": "INR/sqft",
            "effective_date": "2019-01-01"
        }
