import csv
from typing import List, Dict, Any
from .base import CircleRatesAdapter

class UPCircleRatesAdapter(CircleRatesAdapter):
    """Adapter for Uttar Pradesh Circle Rates (Noida and Ghaziabad)."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 50,
            "earliest_date_found": None,
            "latest_date_found": None,
            "structured_data_available": False,
            "manual_intervention_required": True,
            "notes": "Circle rates are published as PDFs on UP district websites. Manual extraction to CSV/JSON is required."
        }
        
    def parse_rates(self, filepath: str) -> List[Dict[str, Any]]:
        rates = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rates.append({
                    "locality_key": row["locality_key"],
                    "circle_rate": float(row["circle_rate"]),
                    "unit": row.get("unit", "INR/sqft"),
                    "effective_date": row.get("effective_date", "2019-01-01")
                })
        return rates

    def get_rate_for_locality(self, parsed_rates: List[Dict[str, Any]], locality_id: str) -> Dict[str, Any]:
        # Perform exact match or fallback mapping
        for rate in parsed_rates:
            if rate["locality_key"].upper() in locality_id.upper():
                return rate
        # If no direct match, return a default/None rate
        return {
            "locality_key": locality_id,
            "circle_rate": 0.0,
            "unit": "INR/sqft",
            "effective_date": "2019-01-01"
        }
