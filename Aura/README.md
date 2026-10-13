# AURA

Autonomous Unified Research & Reasoning Agent.

AURA is a complete local research-agent project with:

- FastAPI backend
- Streamlit frontend
- model routing
- guardrails
- planner, research, RAG, data, verifier, critic, memory, and writer agents
- agent-to-agent message protocol
- hybrid retrieval with vector, keyword, metadata, and web signals
- citation-aware reports
- reflection loop that retrieves again when confidence is low
- local memory
- document upload and URL ingestion
- document-only answering when uploaded documents exist
- automatic web research when no uploaded documents exist
- context window optimizer with token budget controls
- admin dashboard for cost, latency, token, and quality metrics
- LangSmith tracing hooks
- real MCP server with official MCP Python SDK support
- real LangGraph workflow wrapper
- real ChromaDB-backed vector store with JSONL fallback
- HTTP distributed A2A agent service
- MCP tool server and JSON-RPC compatibility endpoints
- trainable intent router for lightweight fine-tuning
- evaluation CLI for retrieval and answer quality metrics

The app works without a paid API key by using deterministic local responses. Add `GROQ_API_KEY` when you want live Groq LLM calls.

## Quick Start

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m aura.scripts.seed_demo
uvicorn aura.api.main:app --reload --reload-dir aura
```

In a second terminal:

```powershell
streamlit run aura/ui/app.py
```

Open:

- API: `http://127.0.0.1:8000/docs`
- UI: the Streamlit URL printed in the terminal

You can also run the UI with:

```powershell
streamlit run aura
```

## Source Modes

AURA chooses the answer source automatically:

- If uploaded document chunks exist, AURA locks into uploaded-documents-only mode and disables URL upload and web research.
- If no uploaded documents exist but URL chunks exist, AURA locks into uploaded-URL-only mode and disables document upload and web research.
- If no documents or URLs exist, AURA enables live web research automatically.

Supported upload types:

```text
pdf, ppt, pptx, doc, docx, xls, xlsx, txt, md, csv, html, htm, json
```

The UI no longer asks for manual document title/content. Upload files or add a URL instead.

## Project Layout

```text
aura/
  agents/      specialized agent nodes
  api/         FastAPI app
  core/        config, LLM gateway, graph, guardrails, A2A protocol
  rag/         ingestion, retrieval, reranking, context budgeting
  memory/      short-term, episodic, and semantic memory
  evals/       evaluation metrics and CLI
  ui/          Streamlit frontend
  tools/       web, filesystem, and data tools
  data/        local documents, reports, memory, vector store
```

## Example Queries

- `Research how agentic RAG differs from basic RAG and cite evidence.`
- `Compare FastAPI and Streamlit responsibilities in this project.`
- `Analyze the CSV aura/data/sample_metrics.csv and summarize trends.`
- `What should AURA remember about my preferred report style?`

## API

```bash
curl -X POST http://127.0.0.1:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"Explain AURA architecture with citations\",\"source_scope\":\"auto\",\"token_budget\":16000}"
```

Useful endpoints:

- `POST /ingest/upload` for files
- `POST /ingest/url` for webpages
- `GET /tools/marketplace` for available MCP-style tools
- `GET /admin/metrics` for cost, latency, token, citation, and confidence metrics
- `GET /capabilities` for LangGraph, ChromaDB, MCP, A2A, and router status

## Evaluation

```powershell
python -m aura.evals.run_eval
```

The evaluation prints retrieval recall, citation coverage, faithfulness proxy, latency, and iteration count.

## Advanced Services

Train the intent router:

```powershell
python -m aura.scripts.train_router
```

Run the optional distributed A2A agent service:

```powershell
uvicorn aura.api.agent_service:app --host 127.0.0.1 --port 8100
```

Then enable it in `.env`:

```env
AURA_DISTRIBUTED_AGENTS=true
AURA_AGENT_BASE_URL=http://127.0.0.1:8100
```

Run the real MCP server using the official MCP Python SDK:

```powershell
python -m aura.mcp_real_server
```

That exposes these MCP tools:

```text
web_search
knowledge_stats
knowledge_ingest_url
knowledge_clear_uploaded
```

Run the optional JSON-RPC compatibility server:

```powershell
uvicorn aura.api.mcp_server:app --host 127.0.0.1 --port 8200
```

Example MCP JSON-RPC call:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8200/mcp `
  -ContentType "application/json" `
  -Body '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

ChromaDB is used automatically through `chromadb.PersistentClient` when available. To connect to a running Chroma server instead:

```env
AURA_CHROMA_HOST=127.0.0.1
AURA_CHROMA_PORT=8001
```

Enable LangSmith tracing by adding your key to `.env`:

```env
LANGSMITH_TRACING=true
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_langsmith_key
LANGCHAIN_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=AURA
LANGCHAIN_PROJECT=AURA
```

Then run AURA normally. Query runs are wrapped in LangSmith traces.

## Notes

This is an extensible educational and portfolio project. The core app now has real LangGraph orchestration, ChromaDB-backed retrieval, HTTP A2A service support, real MCP SDK tooling, LangSmith tracing hooks, admin metrics, and a trainable router classifier.
