# app/models/output_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class VerdictLabel(str, Enum):
    TRUE = "true"
    MOSTLY_TRUE = "mostly_true"
    MIXED = "mixed"
    MOSTLY_FALSE = "mostly_false"
    FALSE = "false"
    UNVERIFIED = "unverified"

class ClaimType(str, Enum):
    FACT = "fact"
    PREDICTION = "prediction"
    OPINION_WITH_FACT_CORE = "opinion_with_fact_core"

class Citation(BaseModel):
    title: str
    url: str
    publisher: str
    date: Optional[str] = None
    quote: Optional[str] = Field(None, max_length=250)

class ModalitiesCheck(BaseModel):
    ooc_risk: bool
    notes: str

class QueryItem(BaseModel):
    query: str
    evidence_type: str
    time_window: Optional[str] = None

class Verdict(BaseModel):
    label: VerdictLabel
    truth_prob: float = Field(..., ge=0.0, le=1.0)
    truth_prob_cal: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    citations: List[Citation] = Field(default_factory=list, max_items=5)
    gaps: List[str]
    modalities_check: ModalitiesCheck

class Claim(BaseModel):
    id: str
    text: str
    type: ClaimType
    prominence: float = Field(..., ge=0.0, le=1.0)
    time_refs: List[str] = []
    named_entities: List[str] = []
    query_plan: List[QueryItem]
    verdict: Verdict
    evidence_strength: float = Field(..., ge=0.0, le=1.0)

class RealityDistance(BaseModel):
    status: Literal["ok", "needs_user_input"]
    value: float = Field(..., ge=0.0, le=100.0)
    notes: str

class BiasContext(BaseModel):
    bias_signals: List[str]
    rhetoric: List[str]
    missing_context: List[str]
    notes: str

class TattvaOutput(BaseModel):
    summary: str
    claims: List[Claim]
    tattva_score: float = Field(..., ge=0.0, le=100.0)
    reality_distance: RealityDistance
    bias_context: BiasContext
    limitations: List[str]