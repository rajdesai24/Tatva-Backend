# app/models/input_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Word(BaseModel):
    text: str
    start: float
    end: float
    confidence: float

class Transcript(BaseModel):
    text: str
    words: Optional[List[Word]] = []

class Metadata(BaseModel):
    source_type: str
    content_length: int
    language_code: str = "en"

class Belief(BaseModel):
    claim_id: str
    p: float = Field(..., ge=0.0, le=1.0)

class TattvaInput(BaseModel):
    status: str
    content_type: str
    transcript: Transcript
    metadata: Metadata
    beliefs: Optional[List[Belief]] = []