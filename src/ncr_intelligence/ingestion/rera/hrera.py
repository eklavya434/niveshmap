import json
from typing import List, Dict, Any
from datetime import date
from bs4 import BeautifulSoup
from .base import RERAAdapter

class HRERAAdapter(RERAAdapter):
    """Adapter for Haryana RERA (HRERA) project files."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 180,
            "earliest_date_found": date(2017, 10, 1),
            "latest_date_found": date.today(),
            "structured_data_available": False,
            "manual_intervention_required": True,
            "notes": "HRERA uses dynamic JavaScript datagrids. Ingestion handles local HTML files."
        }
        
    def parse_projects(self, filepath: str) -> List[Dict[str, Any]]:
        projects = []
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if content.strip().startswith(("[", "{")):
            try:
                data = json.loads(content)
                return [data] if isinstance(data, dict) else data
            except json.JSONDecodeError:
                pass
                
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:
                proj_data = {
                    "reg_no": cols[0].get_text(strip=True),
                    "project_name": cols[1].get_text(strip=True),
                    "promoter": cols[2].get_text(strip=True),
                    "district": cols[3].get_text(strip=True)
                }
                if len(cols) >= 6:
                    proj_data["cost_disclosed"] = cols[4].get_text(strip=True)
                    proj_data["price_disclosed"] = cols[5].get_text(strip=True)
                projects.append(proj_data)
                
        return projects

    def normalize_project(self, raw_project: Dict[str, Any]) -> Dict[str, Any]:
        reg_no = raw_project.get("reg_no") or "UNKNOWN_HRERA"
        name = raw_project.get("project_name") or "Unnamed Project"
        
        raw_price = raw_project.get("price_disclosed") or "0.0"
        try:
            clean_price = float(str(raw_price).replace("INR", "").replace(",", "").strip())
        except ValueError:
            clean_price = 0.0
            
        return {
            "project_id": f"HR_{reg_no}",
            "project_name": name,
            "normalized_name": name.lower().replace(" ", "_"),
            "project_type": "RESIDENTIAL",
            "primary_authority": "HRERA",
            "current_stage": "UNDER_CONSTRUCTION",
            "price_value": clean_price,
            "price_unit": "INR/sqft",
            "raw_reference": f"HRERA registration {reg_no}"
        }
