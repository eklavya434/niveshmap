from abc import abstractmethod
from typing import List, Dict, Any
from ..base import BaseAdapter

class CircleRatesAdapter(BaseAdapter):
    """Abstract interface for all Circle Rate and Collector Rate adapters."""
    
    @abstractmethod
    def parse_rates(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Parses rate schedules from a downloaded gazette PDF or district CSV.
        
        Returns a list of dicts: [{'locality_key': str, 'rate': float, 'unit': str}]
        """
        pass
        
    @abstractmethod
    def get_rate_for_locality(self, parsed_rates: List[Dict[str, Any]], locality_id: str) -> Dict[str, Any]:
        """
        Extracts/maps the circle rate entry for a specific candidate locality.
        """
        pass
