from fastapi import FastAPI
from pydantic import BaseModel, Field

from aura.tools.mcp_registry import MCPToolRegistry

app = FastAPI(title="AURA MCP Tool Server", version="0.1.0")
registry = MCPToolRegistry()


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict = Field(default_factory=dict)


@app.post("/mcp")
def mcp(request: JSONRPCRequest) -> dict:
    try:
        if request.method == "tools/list":
            result = {"tools": registry.list_tools()}
        elif request.method == "tools/call":
            result = registry.call_tool(request.params["name"], request.params.get("arguments", {}))
        else:
            return {"jsonrpc": "2.0", "id": request.id, "error": {"code": -32601, "message": "Method not found"}}
        return {"jsonrpc": "2.0", "id": request.id, "result": result}
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": request.id, "error": {"code": -32000, "message": str(exc)}}
