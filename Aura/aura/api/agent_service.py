from fastapi import FastAPI

from aura.agents.critic import CriticAgent
from aura.agents.data_agent import DataAgent
from aura.agents.planner import PlannerAgent
from aura.agents.rag_agent import RAGAgent
from aura.agents.research import ResearchAgent
from aura.agents.verifier import FactVerifier
from aura.schemas.models import A2AMessage, AgentRole, AgentTrace, Intent

app = FastAPI(title="AURA Distributed Agent Service", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "aura-agent-service"}


@app.post("/a2a/message", response_model=AgentTrace)
def handle_message(message: A2AMessage) -> AgentTrace:
    query = str(message.payload.get("query", message.task))
    if message.receiver == AgentRole.planner:
        intent = Intent(str(message.payload.get("intent", Intent.general.value)))
        _, trace = PlannerAgent().plan(query, intent)
        return trace
    if message.receiver == AgentRole.rag:
        sources, _, trace, _ = RAGAgent().run(query, filters=message.payload.get("filters"))
        trace.output += f" Distributed A2A returned {len(sources)} sources."
        return trace
    if message.receiver == AgentRole.research:
        _, trace = ResearchAgent().run(query, bool(message.payload.get("use_web", False)))
        return trace
    if message.receiver == AgentRole.data:
        _, trace = DataAgent().run(query)
        return trace
    if message.receiver == AgentRole.verifier:
        confidence, trace = FactVerifier().verify(str(message.payload.get("answer", "")), [])
        trace.confidence = confidence
        return trace
    if message.receiver == AgentRole.critic:
        passed, trace = CriticAgent().reflect(str(message.payload.get("answer", "")), [], float(message.payload.get("confidence", 0)))
        trace.output = f"Distributed critic {'PASS' if passed else 'FAIL'}: {trace.output}"
        return trace
    return AgentTrace(agent=message.receiver, input=query, output="No distributed handler registered.", confidence=0.0)
