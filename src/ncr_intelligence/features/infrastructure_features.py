from datetime import date, datetime
from typing import List, Dict, Any, Optional

def parse_quarter_to_date(quarter_str: str) -> date:
    """Converts a quarter string like '2022-Q3' to the end date of that quarter (YYYY-MM-DD)."""
    parts = quarter_str.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid quarter format: {quarter_str}")
    year = int(parts[0])
    q = parts[1]
    
    if q == "Q1":
        return date(year, 3, 31)
    elif q == "Q2":
        return date(year, 6, 30)
    elif q == "Q3":
        return date(year, 9, 30)
    elif q == "Q4":
        return date(year, 12, 31)
    else:
        raise ValueError(f"Invalid quarter specification: {q}")


def get_project_stage_at_quarter(events: List[Dict[str, Any]], target_quarter: str) -> Optional[str]:
    """
    Determines the stage of an infrastructure project as of the end of a given target quarter.
    Prevents temporal leakage by ignoring events that occurred or were published after the quarter.
    
    Each event must contain:
    - 'stage': normalized stage string (e.g. APPROVED, UNDER_CONSTRUCTION)
    - 'event_date': date when the stage transition happened
    - 'article_publish_date': Optional date when the news or document was published.
    """
    target_date = parse_quarter_to_date(target_quarter)
    
    valid_events = []
    for evt in events:
        # Validate event date types
        evt_date = evt["event_date"]
        if isinstance(evt_date, str):
            evt_date = datetime.strptime(evt_date, "%Y-%m-%d").date()
            
        pub_date = evt.get("article_publish_date")
        if isinstance(pub_date, str):
            pub_date = datetime.strptime(pub_date, "%Y-%m-%d").date()
            
        # The event is valid as of target_date ONLY if:
        # 1. The event occurred on or before target_date.
        # 2. The source document/article was published on or before target_date (information availability check).
        if evt_date <= target_date:
            if pub_date is None or pub_date <= target_date:
                valid_events.append((evt_date, pub_date or evt_date, evt["stage"]))
                
    if not valid_events:
        return None
        
    # Sort events by event_date ascending, then by publish date ascending
    valid_events.sort(key=lambda x: (x[0], x[1]))
    
    # Return the stage of the most recent valid event
    return valid_events[-1][2]
