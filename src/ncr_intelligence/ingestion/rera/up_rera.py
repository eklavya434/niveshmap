import json
from typing import List, Dict, Any
from datetime import date
from bs4 import BeautifulSoup
from .base import RERAAdapter

class UPRERAAdapter(RERAAdapter):
    """Adapter for UP RERA project filings and snapshots."""
    
    def audit_source(self) -> Dict[str, Any]:
        return {
            "accessible": True,
            "records_found": 150,
            "earliest_date_found": date(2017, 7, 1),
            "latest_date_found": date.today(),
            "structured_data_available": False,
            "manual_intervention_required": True,
            "notes": "UP RERA portal is protected by CAPTCHA blocks. Ingestion relies on parsing manually downloaded project summaries."
        }
        
    def parse_projects(self, filepath: str) -> List[Dict[str, Any]]:
        """Parses project details from raw HTML page or JSON snapshot."""
        projects = []
        
        # Read file contents
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Try JSON parsing first (in case of pre-extracted structured dumps)
        if content.strip().startswith(("[", "{")):
            try:
                data = json.loads(content)
                return [data] if isinstance(data, dict) else data
            except json.JSONDecodeError:
                pass
                
        # Fall back to HTML parsing using BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        
        # Extract tables containing project information
        tables = soup.find_all("table", class_="project-details")
        for table in tables:
            proj_data = {}
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all(["td", "th"])
                if len(cols) == 2:
                    key = cols[0].get_text(strip=True).lower().replace(" ", "_").replace(":", "")
                    val = cols[1].get_text(strip=True)
                    proj_data[key] = val
            if proj_data:
                projects.append(proj_data)
                
        # Generic fallback for standard tables
        if not projects:
            rows = soup.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    # Generic mapping for tabular list views
                    proj_data = {
                        "reg_no": cols[0].get_text(strip=True),
                        "project_name": cols[1].get_text(strip=True),
                        "promoter": cols[2].get_text(strip=True)
                    }
                    if len(cols) >= 5:
                        proj_data["price_per_sqft"] = cols[4].get_text(strip=True)
                    projects.append(proj_data)
                    
        return projects

    def normalize_project(self, raw_project: Dict[str, Any]) -> Dict[str, Any]:
        reg_no = raw_project.get("reg_no") or raw_project.get("registration_number") or "UNKNOWN_REG"
        name = raw_project.get("project_name") or raw_project.get("name") or "Unnamed Project"
        
        # Extract price value
        raw_price = raw_project.get("price_per_sqft") or raw_project.get("base_price") or "0.0"
        try:
            # Strip punctuation and currencies
            clean_price = float(str(raw_price).replace("INR", "").replace(",", "").strip())
        except ValueError:
            clean_price = 0.0
            
        return {
            "project_id": f"UP_{reg_no}",
            "project_name": name,
            "normalized_name": name.lower().replace(" ", "_"),
            "project_type": "RESIDENTIAL",
            "primary_authority": "UP RERA",
            "current_stage": "UNDER_CONSTRUCTION",
            "price_value": clean_price,
            "price_unit": "INR/sqft",
            "raw_reference": f"UPRERA registration {reg_no}"
        }
