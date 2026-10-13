from typing import Any, TypedDict

from aura.schemas.models import QueryRequest, QueryResponse


class AuraGraphState(TypedDict, total=False):
    request: QueryRequest
    response: QueryResponse
    error: str


class LangGraphAuraApp:
    """Real LangGraph wrapper around AURA's agent workflow."""

    def __init__(self, runner) -> None:
        self.runner = runner
        self.app = self._build()

    def _build(self):
        try:
            from langgraph.graph import END, StateGraph
        except Exception:
            return None

        graph = StateGraph(AuraGraphState)
        graph.add_node("agent_workflow", self._agent_workflow)
        graph.set_entry_point("agent_workflow")
        graph.add_edge("agent_workflow", END)
        return graph.compile()

    def invoke(self, request: QueryRequest) -> QueryResponse:
        if self.app is None:
            return self.runner(request)
        result: dict[str, Any] = self.app.invoke({"request": request})
        return result["response"]

    def _agent_workflow(self, state: AuraGraphState) -> AuraGraphState:
        state["response"] = self.runner(state["request"])
        return state
