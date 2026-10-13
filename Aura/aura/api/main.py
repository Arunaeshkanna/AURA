from fastapi import FastAPI, File, UploadFile

from aura.core.config import get_settings
from aura.core.graph import AuraGraph
from aura.core.metrics import MetricsStore
from aura.core.router_training import FineTunedRouter
from aura.rag.ingest import Ingestor
from aura.rag.store import HybridStore
from aura.schemas.models import DocumentIngestRequest, QueryRequest, QueryResponse, UrlIngestRequest
from aura.tools.marketplace import ToolMarketplace
from aura.tools.mcp_client import AuraMCPClient
from aura.tools.mcp_registry import MCPToolRegistry

settings = get_settings()
app = FastAPI(title="AURA API", version="0.1.0")
graph = AuraGraph()
ingestor = Ingestor()
store = HybridStore()
marketplace = ToolMarketplace()
mcp_registry = MCPToolRegistry()
metrics = MetricsStore()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "store": store.stats()}


@app.get("/capabilities")
def capabilities() -> dict:
    return {
        "langgraph": settings.use_langgraph,
        "chromadb": store.stats().get("chroma_enabled", False),
        "mcp_tools": len(mcp_registry.list_tools()),
        "real_mcp_server": True,
        "distributed_a2a": settings.distributed_agents,
        "fine_tuned_router": settings.router_model_path.exists(),
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return graph.run(request)


@app.post("/ingest")
def ingest(request: DocumentIngestRequest) -> dict:
    count = ingestor.ingest_text(request.title, request.content, request.source, request.metadata)
    return {"ingested_chunks": count}


@app.post("/ingest/upload")
async def ingest_upload(files: list[UploadFile] = File(...)) -> dict:
    total = 0
    processed = []
    for file in files:
        data = await file.read()
        count = ingestor.ingest_upload(file.filename or "uploaded-file", data)
        total += count
        processed.append({"filename": file.filename, "chunks": count})
    return {"ingested_chunks": total, "files": processed}


@app.post("/ingest/url")
def ingest_url(request: UrlIngestRequest) -> dict:
    count = ingestor.ingest_url(request.url, request.title, request.metadata)
    return {"ingested_chunks": count, "url": request.url}


@app.post("/ingest/directory")
def ingest_directory() -> dict:
    count = ingestor.ingest_directory()
    return {"ingested_chunks": count}


@app.get("/stats")
def stats() -> dict:
    return store.stats()


@app.get("/admin/metrics")
def admin_metrics() -> dict:
    return {"summary": metrics.summary(), "runs": metrics.list_runs(100)}


@app.post("/knowledge/clear-uploaded")
def clear_uploaded_knowledge() -> dict:
    removed = store.clear_uploaded()
    return {"removed_chunks": removed}


@app.post("/router/train")
def train_router() -> dict:
    path = FineTunedRouter().train()
    return {"router_model": str(path), "status": "trained"}


@app.get("/tools/marketplace")
def tools_marketplace() -> dict:
    return {"tools": [tool.__dict__ for tool in marketplace.list_tools()]}


@app.get("/mcp/tools")
def mcp_tools() -> dict:
    return {"tools": mcp_registry.list_tools()}


@app.post("/mcp/tools/{tool_name}")
def mcp_call(tool_name: str, arguments: dict | None = None) -> dict:
    return mcp_registry.call_tool(tool_name, arguments or {})


@app.get("/mcp/stdio")
def mcp_stdio_info() -> dict:
    return AuraMCPClient().smoke_check()
