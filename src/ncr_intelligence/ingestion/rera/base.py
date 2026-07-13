from abc import abstractmethod
from typing import List, Dict, Any
from ..base import BaseAdapter

class RERAAdapter(BaseAdapter):
    """Abstract interface for all RERA-specific portal adapters."""
    
    @abstractmethod
    def parse_projects(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Parses raw projects lists or detail views from a snapshot file.
        
        Returns a list of dictionaries containing raw project metrics.
        """
        pass
        
    @abstractmethod
    def normalize_project(self, raw_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes raw portal project fields into standard database models.
        """
        pass
