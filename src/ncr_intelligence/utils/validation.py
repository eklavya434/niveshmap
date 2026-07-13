import re
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

# Target NCR regions allowed
VALID_REGIONS = {
    "Delhi",
    "Noida",
    "Greater Noida",
    "Greater Noida West",
    "Yamuna Expressway / YEIDA / Jewar influence areas",
    "Ghaziabad",
    "Gurugram",
    "Faridabad"
}

# State/UT names allowed
VALID_STATES = {"Delhi", "Uttar Pradesh", "Haryana"}

# Urban maturity classes
VALID_MATURITY_CLASSES = {"MATURE", "TRANSITIONAL", "EMERGING"}

# Infrastructure types
VALID_INFRA_TYPES = {"METRO", "RRTS", "EXPRESSWAY_HIGHWAY", "AIRPORT"}

# Infrastructure stages
VALID_STAGES = {
    "PROPOSED",
    "APPROVED",
    "CONTRACTED",
    "UNDER_CONSTRUCTION",
    "OPERATIONAL",
    "STALLED_DELAYED_CANCELLED"
}

# Price types
VALID_PRICE_TYPES = {
    "transaction",
    "listing",
    "circle_rate",
    "rera_disclosure",
    "index",
    "proxy"
}

# Source quality classes
VALID_QUALITY_CLASSES = {"HIGH", "MEDIUM", "LOW"}


class LocalityValidator(BaseModel):
    locality_id: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    region: str
    state_or_ut: str
    district: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=28.0, le=29.0)
    longitude: float = Field(..., ge=76.5, le=78.0)
    urban_maturity_class: str
    candidate_exposure_types: Optional[List[str]] = Field(default_factory=list)
    candidate_control_group: Optional[bool] = False
    notes: Optional[str] = None

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        if v not in VALID_REGIONS:
            raise ValueError(f"Invalid NCR region: {v}. Must be one of {VALID_REGIONS}")
        return v

    @field_validator("state_or_ut")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v not in VALID_STATES:
            raise ValueError(f"Invalid state/UT: {v}. Must be one of {VALID_STATES}")
        return v

    @field_validator("urban_maturity_class")
    @classmethod
    def validate_maturity(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in VALID_MATURITY_CLASSES:
            raise ValueError(f"Invalid maturity class: {v}. Must be one of {VALID_MATURITY_CLASSES}")
        return v_upper


class SourceValidator(BaseModel):
    source_id: str = Field(..., min_length=2, max_length=50)
    source_name: str = Field(..., min_length=2, max_length=255)
    source_category: str = Field(..., min_length=2, max_length=100)
    geography: str = Field(..., min_length=2, max_length=100)
    official_source: bool = True
    source_url: Optional[str] = None
    access_method: str
    expected_format: str
    historical_depth_notes: Optional[str] = None
    legal_access_notes: Optional[str] = None
    active: bool = True

    @field_validator("access_method")
    @classmethod
    def validate_access_method(cls, v: str) -> str:
        valid_methods = {"api", "html", "pdf", "manual_download"}
        if v not in valid_methods:
            raise ValueError(f"Invalid access method: {v}. Must be one of {valid_methods}")
        return v

    @field_validator("expected_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        valid_formats = {"csv", "json", "html", "pdf", "xlsx"}
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid expected format: {v}. Must be one of {valid_formats}")
        return v.lower()


class PriceObservationValidator(BaseModel):
    locality_id: str = Field(..., min_length=3, max_length=50)
    observation_date: date
    quarter: str
    price_value: float = Field(..., gt=0.0)
    price_unit: str = Field(..., min_length=2, max_length=50)
    price_type: str
    source_id: str = Field(..., min_length=2, max_length=50)
    source_quality_class: str
    is_proxy: bool = False
    raw_reference: Optional[str] = None

    @field_validator("quarter")
    @classmethod
    def validate_quarter(cls, v: str) -> str:
        if not re.match(r"^\d{4}-Q[1-4]$", v):
            raise ValueError(f"Quarter must be in format YYYY-Q# (e.g. 2021-Q3). Got: {v}")
        return v

    @field_validator("price_type")
    @classmethod
    def validate_price_type(cls, v: str) -> str:
        if v not in VALID_PRICE_TYPES:
            raise ValueError(f"Invalid price type: {v}. Must be one of {VALID_PRICE_TYPES}")
        return v

    @field_validator("source_quality_class")
    @classmethod
    def validate_quality_class(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in VALID_QUALITY_CLASSES:
            raise ValueError(f"Invalid quality class: {v}. Must be one of {VALID_QUALITY_CLASSES}")
        return v_upper


class InfrastructureProjectValidator(BaseModel):
    project_id: str = Field(..., min_length=3, max_length=100)
    project_name: str = Field(..., min_length=2, max_length=255)
    normalized_name: str = Field(..., min_length=2, max_length=255)
    project_type: str
    primary_authority: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    current_stage: str

    @field_validator("project_type")
    @classmethod
    def validate_project_type(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in VALID_INFRA_TYPES:
            raise ValueError(f"Invalid project type: {v}. Must be one of {VALID_INFRA_TYPES}")
        return v_upper

    @field_validator("current_stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in VALID_STAGES:
            raise ValueError(f"Invalid stage: {v}. Must be one of {VALID_STAGES}")
        return v_upper


class InfrastructureEventValidator(BaseModel):
    project_id: str = Field(..., min_length=3, max_length=100)
    stage: str
    raw_stage_text: Optional[str] = Field(None, max_length=255)
    event_date: date
    article_publish_date: Optional[date] = None
    evidence_source_id: str = Field(..., min_length=2, max_length=50)
    evidence_strength: float = Field(..., ge=0.0, le=1.0)
    evidence_phrase: Optional[str] = None

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in VALID_STAGES:
            raise ValueError(f"Invalid event stage: {v}. Must be one of {VALID_STAGES}")
        return v_upper
