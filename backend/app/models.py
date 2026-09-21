from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PRIMARY = "PRIMARY"
    NEWS = "NEWS"
    ANALYSIS = "ANALYSIS"
    OFFICIAL = "OFFICIAL"
    UNKNOWN = "UNKNOWN"


class ClaimStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    DISPUTED = "DISPUTED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Source(BaseModel):
    id: str
    title: str
    url: str
    publisher: str
    source_type: SourceType = SourceType.UNKNOWN
    excerpt: str = ""


class Claim(BaseModel):
    statement: str
    evidence: str
    status: ClaimStatus
    source_ids: list[str] = Field(default_factory=list)


class AgentEvent(BaseModel):
    timestamp: datetime
    type: str
    title: str
    detail: str
    status: str = "complete"


class ResearchRequest(BaseModel):
    question: str = Field(min_length=8, max_length=500)


class ResearchReport(BaseModel):
    id: str
    question: str
    executive_summary: str
    established_facts: list[str]
    claims: list[Claim]
    uncertainty: str
    sources: list[Source]
    events: list[AgentEvent]
    iterations: int
    mode: str
