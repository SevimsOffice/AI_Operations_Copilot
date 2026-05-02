"""LangGraph workflow definition for Atlas Operations Copilot."""

from __future__ import annotations

import json
from typing import Literal
from pathlib import Path
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from config.config import load_config
from src.agents.state import CopilotState
from src.tools.analysis_tool import run_operational_analysis
from src.tools.rag_tool import run_rag_query


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # region agent log
    payload = {
        "sessionId": "1129dd",
        "runId": "pre-fix",
        "hypothesisId": hypothesis_id,
        "id": f"log_{uuid4().hex}",
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(__import__("time").time() * 1000),
    }
    log_path = Path(__file__).resolve().parents[2] / "debug-1129dd.log"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    # endregion


def retrieve_context(state: CopilotState) -> CopilotState:
    """Node 1: retrieve semantic context and generate grounded answer."""
    from src.execution.tracer import tracer

    _debug_log(
        "H6",
        "src/agents/graph.py:retrieve_context",
        "Graph retrieve_context node entered",
        {"query": state.get("query", "")[:200]},
    )
    try:
        config = load_config()
        chunks, rag_response = run_rag_query(
            query=state["query"],
            openai_api_key=config.openai_api_key,
            persist_path=config.chroma_persist_path,
            collection_name=config.collection_name,
        )
        print(f"[DEBUG retrieve_context] Got {len(chunks)} chunks")
        print(f"[DEBUG retrieve_context] rag_response type: {type(rag_response)}")
        state["retrieved_chunks"] = chunks
        state["rag_response"] = rag_response
        print(f"[DEBUG retrieve_context] State rag_response set: {state.get('rag_response') is not None}")
    except Exception as e:
        # Log error with context for ops debugging
        tracer.log_error("retrieve_context", e, {
            "query": state.get("query", "")[:200],
            "state_keys": list(state.keys())
        })
        # Set error in state so it can be handled gracefully
        state["error"] = f"Retrieval failed: {str(e)}"
        print(f"[ERROR] retrieve_context failed: {e}")
        import traceback
        traceback.print_exc()
    return state


def generate_answer(state: CopilotState) -> CopilotState:
    """Node 2: validate RAG response exists (retrieval already done in Node 1)."""
    # Architecture note: RAG response is already generated in retrieve_context
    # This node exists to maintain explicit state transition and validation
    rag_resp = state.get("rag_response")
    print(f"[DEBUG generate_answer] rag_response type: {type(rag_resp)}, value: {rag_resp}")

    if rag_resp is None:
        print("[ERROR generate_answer] RAG response is None!")
        state["error"] = "RAG response missing from retrieval step."
    return state


def run_analysis(state: CopilotState) -> CopilotState:
    """Node 3: generate structured operational insights when requested."""
    # Skip analysis if no chunks retrieved or error occurred
    if not state.get("retrieved_chunks") or state.get("error"):
        return state

    state["analysis_report"] = run_operational_analysis(
        query=state["query"],
        retrieved_chunks=state["retrieved_chunks"],
    )
    return state


def format_output(state: CopilotState) -> CopilotState:
    """Node 4: combine RAG and analysis outputs into final state payload."""
    # Architecture note: explicit formatting node keeps response shaping separate
    # from retrieval and reasoning nodes, improving maintainability.
    if state.get("rag_response") is None:
        state["error"] = "RAG response missing."
    return state


def _analysis_route(state: CopilotState) -> Literal["run_analysis", "format_output"]:
    """Route to analysis only when query intent requires deeper insights."""
    trigger_terms = ("bottleneck", "risk", "analyze", "insights")
    query_lower = state["query"].lower()
    if any(term in query_lower for term in trigger_terms):
        return "run_analysis"
    return "format_output"


def build_copilot_graph():
    """Build and compile the LangGraph StateGraph workflow."""
    builder = StateGraph(CopilotState)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("run_analysis", run_analysis)
    builder.add_node("format_output", format_output)

    builder.add_edge(START, "retrieve_context")
    builder.add_edge("retrieve_context", "generate_answer")
    builder.add_conditional_edges(
        "generate_answer",
        _analysis_route,
        {
            "run_analysis": "run_analysis",
            "format_output": "format_output",
        },
    )
    builder.add_edge("run_analysis", "format_output")
    builder.add_edge("format_output", END)
    return builder.compile()
