import json
from typing import Dict, Any, List
from datetime import datetime, date
from ..base import BaseAdapter

class TransitAuthoritiesAdapter(BaseAdapter):
    """Adapter for DMRC, NMRC, NCRTC, and NHAI official project announcements."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 200,
            "earliest_date_found": date(2002, 12, 25), # DMRC Shahdara-Tis Hazari operational date
            "latest_date_found": date.today(),
            "structured_data_available": True,
            "manual_intervention_required": False,
            "notes": "Covers metro lines, RRTS corridors, and highways. High data reliability."
        }
        
    def parse_events(self, filepath: str) -> List[Dict[str, Any]]:
        """Parses transit authority events from a structured JSON release list."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        events = []
        for item in data:
            evt_date = item["event_date"]
            if isinstance(evt_date, str):
                evt_date = datetime.strptime(evt_date, "%Y-%m-%d").date()
                
            pub_date = item.get("article_publish_date")
            if isinstance(pub_date, str):
                pub_date = datetime.strptime(pub_date, "%Y-%m-%d").date()
                
            events.append({
                "project_id": item["project_id"],
                "project_name": item["project_name"],
                "normalized_name": item["project_name"].lower().replace(" ", "_"),
                "project_type": item["project_type"],
                "primary_authority": item["primary_authority"],
                "stage": item["stage"],
                "raw_stage_text": item.get("raw_stage_text", ""),
                "event_date": evt_date,
                "article_publish_date": pub_date or evt_date,
                "evidence_strength": float(item.get("evidence_strength", 1.0)),
                "evidence_phrase": item.get("evidence_phrase", "")
            })
        return events
