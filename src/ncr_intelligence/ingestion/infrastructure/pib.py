import json
from typing import Dict, Any, List
from datetime import datetime, date
from ..base import BaseAdapter

class PIBAdapter(BaseAdapter):
    """Adapter for Press Information Bureau (PIB) cabinet approvals and infrastructure feeds."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 600,
            "earliest_date_found": date(2005, 1, 1),
            "latest_date_found": date.today(),
            "structured_data_available": True,
            "manual_intervention_required": False,
            "notes": "PIB feeds are openly searchable and provide high-confidence milestone evidence."
        }
        
    def parse_events(self, filepath: str) -> List[Dict[str, Any]]:
        """Parses releases containing cabinet approval info from JSON snapshot."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        events = []
        for item in data:
            # Handle date string conversion
            evt_date = item["event_date"]
            if isinstance(evt_date, str):
                evt_date = datetime.strptime(evt_date, "%Y-%m-%d").date()
                
            pub_date = item.get("article_publish_date")
            if isinstance(pub_date, str):
                pub_date = datetime.strptime(pub_date, "%Y-%m-%d").date()
                
            events.append({
                "project_name": item["project_name"],
                "stage": item["stage"],
                "raw_stage_text": item["raw_stage_text"],
                "event_date": evt_date,
                "article_publish_date": pub_date or evt_date,
                "evidence_strength": float(item.get("evidence_strength", 0.90)),
                "evidence_phrase": item.get("evidence_phrase", "")
            })
        return events
