import csv
from typing import List, Dict, Any
from .base import CircleRatesAdapter

class DelhiCircleRatesAdapter(CircleRatesAdapter):
    """Adapter for Delhi circle rates, which are based on category classifications (A to H)."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 8, # 8 categories A-H
            "earliest_date_found": None,
            "latest_date_found": None,
            "structured_data_available": False,
            "manual_intervention_required": True,
            "notes": "Delhi circle rates depend on the locality category class (A to H). Requires mapping categories."
        }
        
    def parse_rates(self, filepath: str) -> List[Dict[str, Any]]:
        rates = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rates.append({
                    "category": row["category"].upper(),
                    "circle_rate": float(row["circle_rate"]),
                    "unit": row.get("unit", "INR/sqft"),
                    "effective_date": row.get("effective_date", "2014-12-05")
                })
        return rates

    def get_rate_for_locality(self, parsed_rates: List[Dict[str, Any]], locality_id: str) -> Dict[str, Any]:
        # Delhi categories mapping lookup
        # Dwarka is Category H/G, Vasant Kunj is Category A/B, etc.
        category_map = {
            "DEL_DWR_SEC10": "H",
            "DEL_VK_SEC_A": "A",
            "DEL_MV_PH1": "E"
        }
        target_cat = category_map.get(locality_id, "H")
        
        for rate in parsed_rates:
            if rate["category"] == target_cat:
                return rate
                
        return {
            "category": "H",
            "circle_rate": 0.0,
            "unit": "INR/sqft",
            "effective_date": "2014-12-05"
        }
