from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Intent(str, Enum):
    general = "general"
    research = "research"
    rag = "rag"
    data = "data"
    coding = "coding"
    memory = "memory"


class AgentRole(str, Enum):
    user = "user"
    planner = "planner"
    research = "research"
    rag = "rag"
    data = "data"
    verifier = "verifier"
    critic = "critic"
    memory = "memory"
    writer = "writer"
    system = "system"


class Source(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    url: str | None = None
    source_type: str = "local"
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0


class Citation(BaseModel):
    source_id: str
    title: str
    url: str | None = None
    snippet: str


class A2AMessage(BaseModel):
    sender: AgentRole
    receiver: AgentRole
    task: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentTrace(BaseModel):
    agent: AgentRole
    input: str
    output: str
    confidence: float = 0.0
    messages: list[A2AMessage] = Field(default_factory=list)


class QueryRequest(BaseModel):
    query: str
    use_web: bool = False
    source_scope: str = "auto"
    autonomous_research: bool = True
    token_budget: int = 16_000
    max_iterations: int = 2
    remember: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    intent: Intent
    confidence: float
    citations: list[Citation] = Field(default_factory=list)
    traces: list[AgentTrace] = Field(default_factory=list)
    iterations: int = 1
    token_budget: int = 18_000
    context_stats: dict[str, Any] = Field(default_factory=dict)
    cost_estimate_usd: float = 0.0
    latency_ms: int = 0


class DocumentIngestRequest(BaseModel):
    title: str
    content: str
    source: str = "manual"
    metadata: dict[str, Any] = Field(default_factory=dict)


class UrlIngestRequest(BaseModel):
    url: str
    title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalResult(BaseModel):
    retrieval_recall: float
    citation_coverage: float
    faithfulness_proxy: float
    answer_relevance: float
    latency_ms: int
    iterations: int
