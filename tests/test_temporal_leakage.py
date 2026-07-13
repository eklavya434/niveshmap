import pytest
from datetime import date
from src.ncr_intelligence.features.infrastructure_features import get_project_stage_at_quarter, parse_quarter_to_date

def test_parse_quarter_to_date():
    assert parse_quarter_to_date("2021-Q1") == date(2021, 3, 31)
    assert parse_quarter_to_date("2022-Q4") == date(2022, 12, 31)
    with pytest.raises(ValueError):
        parse_quarter_to_date("2021-Q5")


def test_temporal_stage_reconstruction():
    # Real-world mock timeline simulation:
    # 2020-Q2: Proposed (announced 2020-05-15, published 2020-05-16)
    # 2021-Q1: Approved (cabinet approval 2021-02-10, published 2021-02-11)
    # 2022-Q3: Under Construction (construction started 2022-08-01, but the official gazette publication was delayed to 2022-10-15 - which is Q4!)
    # 2024-Q2: Operational (commercial run began 2024-05-01, published 2024-05-02)
    
    events = [
        {"stage": "PROPOSED", "event_date": date(2020, 5, 15), "article_publish_date": date(2020, 5, 16)},
        {"stage": "APPROVED", "event_date": date(2021, 2, 10), "article_publish_date": date(2021, 2, 11)},
        {"stage": "UNDER_CONSTRUCTION", "event_date": date(2022, 8, 1), "article_publish_date": date(2022, 10, 15)},
        {"stage": "OPERATIONAL", "event_date": date(2024, 5, 1), "article_publish_date": date(2024, 5, 2)}
    ]
    
    # 1. Before any event (2019-Q4) -> should be None (not yet proposed)
    assert get_project_stage_at_quarter(events, "2019-Q4") is None
    
    # 2. In 2020-Q3 -> PROPOSED
    assert get_project_stage_at_quarter(events, "2020-Q3") == "PROPOSED"
    
    # 3. In 2021-Q2 -> APPROVED
    assert get_project_stage_at_quarter(events, "2021-Q2") == "APPROVED"
    
    # 4. In 2022-Q3 -> APPROVED (Should not leak UNDER_CONSTRUCTION because news publication occurred in Q4/October)
    assert get_project_stage_at_quarter(events, "2022-Q3") == "APPROVED"
    
    # 5. In 2022-Q4 -> UNDER_CONSTRUCTION (Since publication date 2022-10-15 is before end of 2022-Q4)
    assert get_project_stage_at_quarter(events, "2022-Q4") == "UNDER_CONSTRUCTION"
    
    # 6. In 2023-Q4 -> UNDER_CONSTRUCTION
    assert get_project_stage_at_quarter(events, "2023-Q4") == "UNDER_CONSTRUCTION"
    
    # 7. In 2024-Q3 -> OPERATIONAL
    assert get_project_stage_at_quarter(events, "2024-Q3") == "OPERATIONAL"
