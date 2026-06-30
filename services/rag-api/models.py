from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class MessageInput(BaseModel):
    session_id: str
    content: str
    audience: str = "patient"
    user_profile: Optional[dict] = None


class Citation(BaseModel):
    id: str
    title: str
    source: str
    excerpt: str
    relevance_score: float


class AgentTrace(BaseModel):
    agent: str
    action: str
    result: str


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str
    content: str
    citations: list[Citation] = []
    agent_trace: list[AgentTrace] = []
    confidence: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SessionCreate(BaseModel):
    title: Optional[str] = None


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    message_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Topic(BaseModel):
    id: str
    name: str
    description: str
    document_count: int
    icon: str


class Stats(BaseModel):
    total_queries: int
    active_sessions: int
    knowledge_documents: int
    avg_confidence: float
    topics_covered: int
    avg_response_time_ms: int


# ── Risk Assessment ──────────────────────────────────────────────────────────

class RiskInput(BaseModel):
    age: int = Field(..., ge=18, le=110)
    education_years: int = Field(..., ge=0, le=30)
    apoe4_alleles: int = Field(0, ge=0, le=2)   # 0 = none, 1 = heterozygous, 2 = homozygous
    hypertension: bool = False
    obesity: bool = False
    smoking: bool = False
    depression: bool = False
    physical_inactivity: bool = False
    diabetes: bool = False
    social_isolation: bool = False
    hearing_loss: bool = False
    excess_alcohol: bool = False
    tbi_history: bool = False
    high_cholesterol: bool = False
    vision_loss: bool = False


class ShapAttribution(BaseModel):
    feature: str
    key: str
    value: float
    shap_value: float
    impact: str


class RiskResult(BaseModel):
    risk_category: str
    risk_color: str
    probabilities: dict
    top_attributions: list[ShapAttribution]
    disclaimer: str
