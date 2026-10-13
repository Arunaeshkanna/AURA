import json

import requests
import streamlit as st


st.set_page_config(page_title="AURA", page_icon="A", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
  background:
    radial-gradient(circle at 12% 0%, rgba(45, 212, 191, 0.18), transparent 28%),
    radial-gradient(circle at 92% 6%, rgba(96, 165, 250, 0.16), transparent 30%),
    linear-gradient(135deg, #070a12 0%, #0d1424 52%, #101827 100%);
  color: #edf5ff;
}

.block-container {
  max-width: 1320px;
  padding-top: 1.4rem;
  padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
  background: rgba(8, 13, 23, 0.98);
  border-right: 1px solid rgba(148, 163, 184, 0.18);
}

[data-testid="stSidebar"] * { color: #edf5ff; }

.hero {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 10px;
  padding: 30px;
  background:
    linear-gradient(135deg, rgba(45, 212, 191, 0.18), rgba(96, 165, 250, 0.10)),
    rgba(15, 23, 42, 0.78);
  box-shadow: 0 26px 70px rgba(0, 0, 0, 0.30);
}

.eyebrow {
  color: #5eead4;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.title {
  color: #ffffff;
  font-size: clamp(2.4rem, 5vw, 4.8rem);
  font-weight: 800;
  line-height: 0.95;
  margin: 7px 0 10px;
}

.subtitle {
  color: #b8c7dd;
  max-width: 780px;
  font-size: 1.02rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0 20px;
}

.card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 10px;
  padding: 16px;
  background: rgba(15, 23, 42, 0.72);
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.22);
}

.label {
  color: #9fb0c8;
  font-size: 0.78rem;
  font-weight: 700;
}

.value {
  color: #ffffff;
  font-size: 1.28rem;
  font-weight: 800;
  margin-top: 5px;
}

.panel {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 10px;
  padding: 18px;
  background: rgba(15, 23, 42, 0.74);
  box-shadow: 0 16px 42px rgba(0, 0, 0, 0.22);
  margin-bottom: 14px;
}

.panel-title {
  color: #ffffff;
  font-size: 1rem;
  font-weight: 800;
  margin-bottom: 8px;
}

.muted { color: #aebbd1; font-size: 0.92rem; }

.source-pill {
  display: inline-block;
  padding: 7px 11px;
  border-radius: 999px;
  border: 1px solid rgba(94, 234, 212, 0.40);
  color: #99f6e4;
  background: rgba(20, 184, 166, 0.10);
  font-weight: 800;
  font-size: 0.82rem;
}

.mode-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 16px 0;
}

.mode-box {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 10px;
  padding: 14px;
  background: rgba(15, 23, 42, 0.62);
}

.mode-box.active {
  border-color: rgba(94, 234, 212, 0.65);
  background: rgba(20, 184, 166, 0.13);
}

.mode-box.disabled {
  opacity: 0.48;
}

.mode-name {
  color: #ffffff;
  font-weight: 800;
  margin-bottom: 5px;
}

.citation {
  border-left: 3px solid #5eead4;
  border-radius: 0 10px 10px 0;
  background: rgba(15, 23, 42, 0.72);
  padding: 12px 14px;
  margin: 10px 0;
}

.trace {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.72);
  padding: 12px 14px;
  margin: 9px 0;
}

.trace-role {
  color: #86efac;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.stButton > button {
  border-radius: 10px;
  border: 1px solid rgba(94, 234, 212, 0.45);
  background: linear-gradient(135deg, #2dd4bf, #60a5fa);
  color: #04111f;
  font-weight: 800;
  min-height: 44px;
}

textarea, input { border-radius: 10px !important; }

@media (max-width: 900px) {
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
"""


def get_health(api_url: str) -> dict:
    try:
        return requests.get(f"{api_url}/health", timeout=3).json()
    except Exception:
        return {}


def active_mode(store: dict) -> tuple[str, bool, str]:
    docs = store.get("uploaded_documents", 0)
    urls = store.get("uploaded_links", 0)
    if docs > 0:
        return "documents", False, "Uploaded documents only"
    if urls > 0:
        return "urls", False, "Uploaded URL only"
    return "web", True, "Live web research"


def render_mode_dashboard(source_scope: str, store: dict) -> None:
    docs_class = "active" if source_scope == "documents" else "disabled"
    urls_class = "active" if source_scope == "urls" else "disabled"
    web_class = "active" if source_scope == "web" else "disabled"
    st.markdown(
        f"""
        <div class="mode-board">
          <div class="mode-box {docs_class}">
            <div class="mode-name">Uploaded Documents</div>
            <div class="muted">{store.get("uploaded_documents", 0)} chunks</div>
          </div>
          <div class="mode-box {urls_class}">
            <div class="mode-name">Uploaded URL</div>
            <div class="muted">{store.get("uploaded_links", 0)} chunks</div>
          </div>
          <div class="mode-box {web_class}">
            <div class="mode-name">Web Research</div>
            <div class="muted">{"enabled" if source_scope == "web" else "disabled"}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def api_post(url: str, payload: dict, timeout: int = 180) -> requests.Response:
    return requests.post(url, json=payload, timeout=timeout)


def api_upload(url: str, uploaded_files: list, timeout: int = 180) -> requests.Response:
    files = [
        ("files", (file.name, file.getvalue(), file.type or "application/octet-stream"))
        for file in uploaded_files
    ]
    return requests.post(url, files=files, timeout=timeout)


def set_query(text: str) -> None:
    st.session_state.query_text = text


def render_cards(data: dict | None, mode_label: str) -> None:
    intent = data.get("intent", "ready") if data else "ready"
    confidence = f"{data.get('confidence', 0):.2f}" if data else "--"
    iterations = data.get("iterations", "--") if data else "--"
    latency = f"{data.get('latency_ms', 0)} ms" if data else "--"
    st.markdown(
        f"""
        <div class="grid">
          <div class="card"><div class="label">Mode</div><div class="value">{mode_label}</div></div>
          <div class="card"><div class="label">Intent</div><div class="value">{intent}</div></div>
          <div class="card"><div class="label">Confidence</div><div class="value">{confidence}</div></div>
          <div class="card"><div class="label">Latency</div><div class="value">{latency}</div></div>
        </div>
        <div class="grid" style="grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: -8px;">
          <div class="card"><div class="label">Self-correction loops</div><div class="value">{iterations}</div></div>
          <div class="card"><div class="label">Source rule</div><div class="value">Automatic</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_context_stats(data: dict | None) -> None:
    if not data:
        return
    stats = data.get("context_stats", {})
    st.markdown(
        f"""
        <div class="panel">
          <div class="panel-title">Context Optimizer</div>
          <div class="muted">
            Budget {stats.get("available_tokens", data.get("token_budget", 0))} tokens.
            Sources in {stats.get("input_sources", 0)}.
            Kept {stats.get("kept_sources", 0)}.
            Duplicates removed {stats.get("duplicates_removed", 0)}.
            Weak removed {stats.get("weak_removed", 0)}.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_citations(citations: list[dict]) -> None:
    if not citations:
        st.info("No citations were returned for this answer.")
        return
    for idx, citation in enumerate(citations, start=1):
        url = citation.get("url") or "local knowledge base"
        st.markdown(
            f"""
            <div class="citation">
              <strong>[{idx}] {citation.get("title", "Source")}</strong><br>
              <span class="muted">{url}</span><br><br>
              {citation.get("snippet", "")}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_traces(traces: list[dict]) -> None:
    if not traces:
        st.info("Run a query to see the agent trace.")
        return
    for trace in traces:
        st.markdown(
            f"""
            <div class="trace">
              <div class="trace-role">{trace.get("agent", "agent")}</div>
              <div>{trace.get("output", "")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_admin(api_url: str) -> None:
    try:
        metrics = requests.get(f"{api_url}/admin/metrics", timeout=5).json()
        caps = requests.get(f"{api_url}/capabilities", timeout=5).json()
    except Exception:
        st.info("Start the backend to view admin metrics.")
        return
    summary = metrics.get("summary", {})
    st.markdown("#### Operations Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Runs", summary.get("runs", 0))
    c2.metric("Avg latency", f"{summary.get('avg_latency_ms', 0)} ms")
    c3.metric("Avg confidence", summary.get("avg_confidence", 0))
    c4.metric("Tokens est.", summary.get("total_tokens_est", 0))
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Cost est.", f"${summary.get('total_cost_estimate_usd', 0)}")
    c6.metric("Avg loops", summary.get("avg_iterations", 0))
    c7.metric("Citation rate", summary.get("citation_rate", 0))
    c8.metric("MCP tools", caps.get("mcp_tools", 0))
    st.markdown("#### System Capabilities")
    st.json(caps)
    runs = metrics.get("runs", [])
    if runs:
        st.markdown("#### Recent Runs")
        st.dataframe(runs[::-1], use_container_width=True)


st.markdown(CSS, unsafe_allow_html=True)

if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "query_text" not in st.session_state:
    st.session_state.query_text = ""

with st.sidebar:
    st.markdown("### AURA")
    API_URL = st.text_input("API URL", "http://127.0.0.1:8000")

    health = get_health(API_URL)
    store = health.get("store", {})
    source_scope, use_web, mode_label = active_mode(store)
    docs_locked = source_scope == "documents"
    urls_locked = source_scope == "urls"

    if health:
        st.success("Backend online")
        st.caption(
            f"Files: {store.get('uploaded_documents', 0)} chunks | "
            f"URLs: {store.get('uploaded_links', 0)} chunks"
        )
        if store.get("uploaded_documents", 0) or store.get("uploaded_links", 0):
            if st.button("Clear uploaded knowledge", use_container_width=True):
                res = requests.post(f"{API_URL}/knowledge/clear-uploaded", timeout=30)
                if res.ok:
                    st.success(f"Removed {res.json().get('removed_chunks', 0)} chunks.")
                    st.rerun()
                else:
                    st.error(res.text)
    else:
        st.error("Backend offline. Start FastAPI first.")

    st.markdown("### Add Knowledge")
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "ppt", "pptx", "doc", "docx", "xls", "xlsx", "txt", "md", "csv", "html", "htm", "json"],
        accept_multiple_files=True,
        disabled=urls_locked,
        help="Disabled while URL-only mode is active. Clear uploaded knowledge to switch sources." if urls_locked else None,
    )
    if urls_locked:
        st.caption("Document upload is disabled because URL-only mode is active.")
    if st.button("Index uploaded files", use_container_width=True, disabled=urls_locked or not uploaded_files):
        try:
            res = api_upload(f"{API_URL}/ingest/upload", uploaded_files)
            if res.ok:
                st.success(f"Indexed {res.json().get('ingested_chunks', 0)} chunks.")
                st.rerun()
            st.error(res.text) if not res.ok else None
        except Exception as exc:
            st.error(f"Upload failed: {exc}")

    url_value = st.text_input(
        "Add URL",
        placeholder="https://example.com/page",
        disabled=docs_locked,
        help="Disabled while document-only mode is active. Clear uploaded knowledge to switch sources." if docs_locked else None,
    )
    if docs_locked:
        st.caption("URL upload is disabled because document-only mode is active.")
    if st.button("Index URL", use_container_width=True, disabled=docs_locked or not url_value.strip()):
        try:
            res = api_post(f"{API_URL}/ingest/url", {"url": url_value.strip()}, timeout=60)
            if res.ok:
                st.success(f"Indexed {res.json().get('ingested_chunks', 0)} chunks.")
                st.rerun()
            st.error(res.text) if not res.ok else None
        except Exception as exc:
            st.error(f"URL ingest failed: {exc}")

    with st.expander("Advanced"):
        autonomous_research = st.toggle("Autonomous research", value=True)
        remember = st.toggle("Learning memory", value=True)
        max_iterations = st.slider("Self-correction loops", 1, 4, 2)
        token_budget = st.slider("Context token budget", 4_000, 32_000, 16_000, step=1_000)
        try:
            caps = requests.get(f"{API_URL}/capabilities", timeout=5).json()
            st.caption(
                f"LangGraph: {caps.get('langgraph')} | "
                f"ChromaDB: {caps.get('chromadb')} | "
                f"MCP tools: {caps.get('mcp_tools')} | "
                f"A2A: {caps.get('distributed_a2a')} | "
                f"Router trained: {caps.get('fine_tuned_router')}"
            )
        except Exception:
            st.caption("Capabilities unavailable until backend is running.")
        if st.button("Train router classifier", use_container_width=True):
            res = requests.post(f"{API_URL}/router/train", timeout=60)
            if res.ok:
                st.success("Router classifier trained.")
            else:
                st.error(res.text)

    with st.expander("Tool Marketplace"):
        try:
            tools = requests.get(f"{API_URL}/tools/marketplace", timeout=5).json().get("tools", [])
            for tool in tools:
                st.markdown(f"**{tool['name']}**")
                st.caption(f"{tool['status']} - {tool['description']}")
        except Exception:
            st.caption("Start backend to view tools.")

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Autonomous Unified Research Agent</div>
      <div class="title">AURA</div>
      <div class="subtitle">
        Upload documents, index a URL, or ask directly. AURA automatically chooses the right source:
        documents only, URL only, or live web research.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_cards(st.session_state.last_response, mode_label)
render_mode_dashboard(source_scope, store)
render_context_stats(st.session_state.last_response)

main_col, side_col = st.columns([1.6, 0.8], gap="large")

with main_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Ask AURA</div>', unsafe_allow_html=True)
    query = st.text_area(
        "Ask AURA",
        key="query_text",
        label_visibility="collapsed",
        height=150,
        placeholder="Ask anything. AURA will automatically use uploaded documents, uploaded URL content, or web research.",
    )

    b1, b2, b3 = st.columns(3)
    with b1:
        st.button("Explain El Nino", use_container_width=True, on_click=set_query, args=("Explain El Nino and its effects.",))
    with b2:
        st.button("Summarize source", use_container_width=True, on_click=set_query, args=("Summarize the available source material with citations.",))
    with b3:
        st.button("Find evidence", use_container_width=True, on_click=set_query, args=("Find the strongest evidence and explain it clearly.",))

    run = st.button("Run AURA", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with side_col:
    st.markdown(
        f"""
        <div class="panel">
          <div class="panel-title">Detected Source Mode</div>
          <span class="source-pill">{mode_label}</span>
          <div class="muted" style="margin-top: 12px;">
            {"Web disabled. Answering only from uploaded documents." if source_scope == "documents" else ""}
            {"Web disabled. Answering only from indexed URL content." if source_scope == "urls" else ""}
            {"No documents or URLs found. AURA will use live web research." if source_scope == "web" else ""}
          </div>
        </div>
        <div class="panel">
          <div class="panel-title">Source Priority</div>
          <div class="muted">
            1. Uploaded documents<br>
            2. Uploaded URL content<br>
            3. Live web research
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if run and query.strip():
    payload = {
        "query": query,
        "use_web": use_web,
        "source_scope": source_scope,
        "autonomous_research": autonomous_research,
        "token_budget": token_budget,
        "max_iterations": max_iterations,
        "remember": remember,
    }
    with st.spinner("AURA is retrieving, optimizing, verifying, and writing..."):
        try:
            response = api_post(f"{API_URL}/query", payload)
        except Exception as exc:
            response = None
            st.error(f"Could not reach backend: {exc}")

    if response is not None and response.ok:
        st.session_state.last_response = response.json()
        st.rerun()
    elif response is not None:
        st.error(response.text)

data = st.session_state.last_response
tabs = st.tabs(["Answer", "Citations", "Agent Process", "Admin", "JSON"])

with tabs[0]:
    if data:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(data["answer"])
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class="panel">
              <div class="panel-title">Ready</div>
              <div class="muted">Ask a question to see AURA's answer here.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tabs[1]:
    render_citations(data.get("citations", []) if data else [])

with tabs[2]:
    render_traces(data.get("traces", []) if data else [])

with tabs[3]:
    render_admin(API_URL)

with tabs[4]:
    if data:
        st.code(json.dumps(data, indent=2), language="json")
    else:
        st.info("No response yet.")
