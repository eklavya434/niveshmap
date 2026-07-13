from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAdapter(ABC):
    """Abstract base class for all data source adapters in the system."""
    
    def __init__(self, source_config: Dict[str, Any]):
        self.source_config = source_config
        self.source_id = source_config["source_id"]
        self.status = source_config.get("status", "not_audited")
        
    @abstractmethod
    def audit_source(self) -> Dict[str, Any]:
        """
        Audits the feasibility of connecting to and parsing the source.
        
        Returns a dictionary with the following structure:
        {
            "accessible": bool,
            "records_found": int,
            "earliest_date_found": date or None,
            "latest_date_found": date or None,
            "structured_data_available": bool,
            "manual_intervention_required": bool,
            "notes": str
        }
        """
        pass
