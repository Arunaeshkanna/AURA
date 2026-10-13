import time

from aura.agents.critic import CriticAgent
from aura.agents.data_agent import DataAgent
from aura.agents.memory_agent import MemoryAgent
from aura.agents.planner import PlannerAgent
from aura.agents.rag_agent import RAGAgent
from aura.agents.research import ResearchAgent
from aura.agents.verifier import FactVerifier
from aura.agents.writer import WriterAgent
from aura.core.a2a import A2ABus
from aura.core.distributed_a2a import DistributedA2AClient
from aura.core.guardrails import Guardrails
from aura.core.langgraph_app import LangGraphAuraApp
from aura.core.llm import ModelRouter
from aura.core.metrics import MetricsStore
from aura.core.tracing import aura_trace
from aura.rag.retriever import ContextBudgeter
from aura.rag.store import HybridStore
from aura.schemas.models import A2AMessage, AgentRole, AgentTrace, QueryRequest, QueryResponse, Source


class AuraGraph:
    def __init__(self) -> None:
        self.guardrails = Guardrails()
        self.router = ModelRouter()
        self.planner = PlannerAgent()
        self.research = ResearchAgent()
        self.rag = RAGAgent()
        self.data = DataAgent()
        self.verifier = FactVerifier()
        self.critic = CriticAgent()
        self.writer = WriterAgent()
        self.memory = MemoryAgent()
        self.budgeter = ContextBudgeter()
        self.store = HybridStore()
        self.distributed_a2a = DistributedA2AClient()
        self.metrics = MetricsStore()
        self._langgraph_app = None

    def run(self, request: QueryRequest) -> QueryResponse:
        with aura_trace(
            "aura_query",
            inputs={"query": request.query, "source_scope": request.source_scope},
            metadata={"max_iterations": request.max_iterations, "token_budget": request.token_budget},
        ):
            if self.store.settings.use_langgraph:
                if self._langgraph_app is None:
                    self._langgraph_app = LangGraphAuraApp(self._run_linear)
                response = self._langgraph_app.invoke(request)
            else:
                response = self._run_linear(request)
            self.metrics.record(request, response)
            return response

    def _run_linear(self, request: QueryRequest) -> QueryResponse:
        started = time.perf_counter()
        bus = A2ABus()
        traces = []
        checked = self.guardrails.check_input(request.query)
        if not checked.allowed:
            return QueryResponse(
                answer=f"Request blocked by input guardrails: {', '.join(checked.reasons)}",
                intent=self.router.classify(request.query),
                confidence=0.0,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

        query = checked.sanitized
        intent = self.router.classify(query)
        _, trace = self.planner.plan(query, intent)
        remote_trace = self.distributed_a2a.call(
            A2AMessage(
                sender=AgentRole.planner,
                receiver=AgentRole.planner,
                task="plan",
                payload={"query": query, "intent": intent.value},
            )
        )
        if remote_trace is not None:
            trace = remote_trace
        traces.append(trace)
        bus.send(A2AMessage(sender=AgentRole.planner, receiver=AgentRole.rag, task="retrieve", payload={"query": query}))

        all_sources: list[Source] = []
        iterations = 0
        answer = ""
        citations = []
        confidence = 0.0
        context_stats = {
            "available_tokens": request.token_budget,
            "input_sources": 0,
            "kept_sources": 0,
            "duplicates_removed": 0,
            "weak_removed": 0,
        }
        store_stats = self.store.stats()
        uploaded_documents = store_stats.get("uploaded_documents", 0)
        uploaded_links = store_stats.get("uploaded_links", 0)
        source_scope = self._resolve_source_scope(request.source_scope, uploaded_documents, uploaded_links)
        rag_filters = self._filters_for_scope(source_scope)
        use_web = self._should_use_web(request, source_scope)
        source_only = source_scope in {"documents", "urls"}
        max_iterations = max(1, request.max_iterations if request.autonomous_research else 1)

        memory_context, memory_trace = self.memory.recall()
        traces.append(memory_trace)

        for iteration in range(max_iterations):
            iterations = iteration + 1
            local_sources, context, rag_trace, rag_stats = self.rag.run(
                query,
                filters=rag_filters,
                token_budget=request.token_budget,
                preserve_weak=source_only,
            )
            remote_rag_trace = self.distributed_a2a.call(
                A2AMessage(
                    sender=AgentRole.planner,
                    receiver=AgentRole.rag,
                    task="retrieve",
                    payload={"query": query, "filters": rag_filters},
                )
            )
            if remote_rag_trace is not None:
                rag_trace.output += f" Remote A2A: {remote_rag_trace.output}"
            traces.append(rag_trace)
            all_sources = self._dedupe(all_sources + local_sources)
            context_stats.update(rag_stats)

            if source_scope in {"documents", "urls"} and not all_sources:
                source_label = "uploaded documents" if source_scope == "documents" else "uploaded URL content"
                answer = (
                    f"AURA detected {source_label} mode and kept live web search disabled. "
                    f"I could not find any indexed chunks inside the {source_label}. "
                    "Add the source again or clear uploaded knowledge to switch back to web research."
                )
                confidence = 0.0
                break

            if intent.value == "data":
                data_sources, data_trace = self.data.run(query)
                traces.append(data_trace)
                all_sources = self._dedupe(all_sources + data_sources)

            web_sources, research_trace = self.research.run(query, use_web and iteration == 0)
            traces.append(research_trace)
            all_sources = self._dedupe(all_sources + web_sources)

            optimized_sources, context_stats = self.budgeter.optimize(
                all_sources,
                request.token_budget,
                preserve_weak=source_only,
            )
            all_sources = optimized_sources
            full_context = self.budgeter.compress(all_sources, request.token_budget, preserve_weak=source_only)
            if memory_context:
                full_context += f"\n\n[Memory]\n{memory_context}"

            answer, citations, writer_trace = self.writer.write(query, intent, full_context or context, all_sources)
            traces.append(writer_trace)

            confidence, verifier_trace = self.verifier.verify(answer, all_sources)
            traces.append(verifier_trace)
            citation_score, citation_note = self.verifier.verify_citations(all_sources)
            traces.append(
                AgentTrace(
                    agent=AgentRole.verifier,
                    input="citations",
                    output=citation_note,
                    confidence=citation_score,
                )
            )

            passed, critic_trace = self.critic.reflect(answer, all_sources, confidence)
            traces.append(critic_trace)
            bus.send(
                A2AMessage(
                    sender=AgentRole.critic,
                    receiver=AgentRole.planner if not passed else AgentRole.writer,
                    task="reflection",
                    payload={"passed": passed, "confidence": confidence},
                )
            )
            if passed:
                break
            query = f"{request.query} missing evidence unresolved aspects"

        checked_output = self.guardrails.check_output(answer, len(citations))
        if not checked_output.allowed:
            answer += f"\n\nOutput guardrail notes: {', '.join(checked_output.reasons)}"

        if request.remember:
            traces.append(self.memory.remember_interaction(request.query, answer))

        for trace in traces:
            trace.messages = bus.inbox(trace.agent)

        return QueryResponse(
            answer=answer,
            intent=intent,
            confidence=confidence,
            citations=citations,
            traces=traces,
            iterations=iterations,
            token_budget=request.token_budget,
            context_stats=context_stats,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def _dedupe(self, sources: list[Source]) -> list[Source]:
        seen = {}
        for source in sources:
            key = (source.title, source.url, source.content[:80])
            if key not in seen or source.score > seen[key].score:
                seen[key] = source
        return list(seen.values())

    def _filters_for_scope(self, source_scope: str) -> dict | None:
        if source_scope == "documents":
            return {"uploaded_kind": "document"}
        if source_scope == "urls":
            return {"collection": "web_uploads"}
        return None

    def _resolve_source_scope(self, requested_scope: str, uploaded_documents: int, uploaded_links: int) -> str:
        requested = requested_scope.lower().strip()
        if requested in {"documents", "urls", "web"}:
            return requested
        if uploaded_documents > 0:
            return "documents"
        if uploaded_links > 0:
            return "urls"
        return "web"

    def _should_use_web(self, request: QueryRequest, source_scope: str) -> bool:
        if source_scope in {"documents", "urls"}:
            return False
        if source_scope == "web":
            return True
        return request.use_web
