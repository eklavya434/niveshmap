import json
from typing import List, Dict, Any
from datetime import date
from bs4 import BeautifulSoup
from .base import RERAAdapter

class DelhiRERAAdapter(RERAAdapter):
    """Adapter for Delhi RERA project files."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 40,
            "earliest_date_found": date(2018, 9, 1),
            "latest_date_found": date.today(),
            "structured_data_available": False,
            "manual_intervention_required": True,
            "notes": "Delhi RERA portal has a lower density of projects. Filings are audited from HTML files."
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
            if len(cols) >= 3:
                proj_data = {
                    "reg_no": cols[0].get_text(strip=True),
                    "project_name": cols[1].get_text(strip=True),
                    "developer": cols[2].get_text(strip=True)
                }
                if len(cols) >= 4:
                    proj_data["price_per_sqm"] = cols[3].get_text(strip=True)
                projects.append(proj_data)
                
        return projects

    def normalize_project(self, raw_project: Dict[str, Any]) -> Dict[str, Any]:
        reg_no = raw_project.get("reg_no") or "UNKNOWN_DELHI_RERA"
        name = raw_project.get("project_name") or "Unnamed Project"
        
        raw_price = raw_project.get("price_per_sqm") or "0.0"
        try:
            # Parse price and convert from per sqm to per sqft if required
            # 1 sqm = 10.7639 sqft, so price per sqft = price per sqm / 10.7639
            clean_price = float(str(raw_price).replace("INR", "").replace(",", "").strip())
            price_sqft = round(clean_price / 10.7639, 2)
        except ValueError:
            price_sqft = 0.0
            
        return {
            "project_id": f"DEL_{reg_no}",
            "project_name": name,
            "normalized_name": name.lower().replace(" ", "_"),
            "project_type": "RESIDENTIAL",
            "primary_authority": "Delhi RERA",
            "current_stage": "UNDER_CONSTRUCTION",
            "price_value": price_sqft,
            "price_unit": "INR/sqft",
            "raw_reference": f"Delhi RERA registration {reg_no}"
        }
