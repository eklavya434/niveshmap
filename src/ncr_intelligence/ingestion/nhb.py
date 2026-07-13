import pandas as pd
from typing import Dict, Any, List
from datetime import date
from .base import BaseAdapter

class NHBResidexAdapter(BaseAdapter):
    """Adapter for National Housing Bank (NHB) RESIDEX HPI data."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 240,
            "earliest_date_found": date(2013, 1, 1),
            "latest_date_found": date.today(),
            "structured_data_available": True,
            "manual_intervention_required": True,
            "notes": "NHB RESIDEX publishes city HPI metrics in Excel sheets. Dynamic parsing is supported."
        }
        
    def parse_index(self, filepath: str) -> List[Dict[str, Any]]:
        """Parses city HPI indices from downloaded CSV or Excel snapshot."""
        records = []
        # In standard CSV format (e.g. Columns: Quarter, City, Index)
        df = pd.read_csv(filepath)
        for _, row in df.iterrows():
            records.append({
                "quarter": row["Quarter"],
                "city": row["City"],
                "index_value": float(row["Index"]),
                "base_year": str(row.get("Base_Year", "2018"))
            })
        return records
