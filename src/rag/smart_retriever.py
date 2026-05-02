"""Smart retrieval strategies based on query type."""

from __future__ import annotations

import json
from typing import Any
from pathlib import Path
from uuid import uuid4

from openai import OpenAI

from src.rag.embedder import build_openai_embedder
from src.rag.query_classifier import QueryType, classify_query, infer_source_type
from src.rag.vector_store import get_chroma_collection, search_similar_chunks
from src.execution.validator import validate_retrieval_result
from src.execution.tracer import tracer


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
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
    log_path = Path(__file__).resolve().parents[3] / "debug-1129dd.log"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    # endregion


def smart_retrieve(
    query: str,
    openai_api_key: str,
    persist_path: str,
    collection_name: str,
) -> list[dict[str, Any]]:
    """Intelligent retrieval that adapts strategy based on query type.

    Args:
        query: User's query
        openai_api_key: OpenAI API key
        persist_path: ChromaDB path
        collection_name: Collection name

    Returns:
        Retrieved chunks optimized for the query type
    """
    # Classify the query with error handling
    try:
        query_type = classify_query(query)
        source_hint = infer_source_type(query)

        # Log classification
        tracer.log("classification", {
            "query": query[:100],
            "query_type": query_type.value,
            "source_hint": source_hint
        })
    except Exception as e:
        # Log classification failure with context
        tracer.log_error("classification", e, {
            "query": query[:200],
            "csv_indicators": ["complaint", "complain", "record", "transaction", "item", "order", "status"],
            "crm_indicators": ["customer", "account", "client", "company", "contact"]
        })
        raise  # Re-raise so caller knows it failed

    # VALIDATION: source_hint must be deterministic for COUNTING/LISTING
    if source_hint is None and query_type in [QueryType.COUNTING, QueryType.LISTING]:
        raise ValueError(
            f"Cannot perform {query_type.value} query without clear source type. "
            f"Query: '{query}'"
        )

    _debug_log(
        "H1_H2",
        "src/rag/smart_retriever.py:smart_retrieve",
        "Query classification and source hint",
        {"query": query[:200], "query_type": query_type.value, "source_hint": source_hint},
    )

    print(f"[SMART RETRIEVAL] Query type: {query_type.value}, Source hint: {source_hint}")

    # Route to appropriate retrieval strategy
    if query_type == QueryType.COUNTING:
        chunks = _counting_retrieval(
            query, openai_api_key, persist_path, collection_name, source_hint
        )
    elif query_type == QueryType.LISTING:
        chunks = _listing_retrieval(
            query, openai_api_key, persist_path, collection_name, source_hint
        )
    else:
        chunks = _semantic_retrieval(
            query, openai_api_key, persist_path, collection_name
        )

    # VALIDATE before returning
    validate_retrieval_result(query, query_type, source_hint, chunks)

    # Log retrieval completion
    source_types = {}
    for c in chunks:
        src_type = c.get('metadata', {}).get('source_type', 'unknown')
        source_types[src_type] = source_types.get(src_type, 0) + 1

    tracer.log("retrieval_complete", {
        "chunk_count": len(chunks),
        "source_types": source_types
    })

    return chunks


def _counting_retrieval(
    query: str,
    openai_api_key: str,
    persist_path: str,
    collection_name: str,
    source_hint: str | None,
) -> list[dict[str, Any]]:
    """Retrieval strategy for counting queries.

    For counting, we need ALL relevant records, not just top-K.
    """
    collection = get_chroma_collection(persist_path, collection_name)
    _debug_log(
        "H3_H5",
        "src/rag/smart_retriever.py:_counting_retrieval",
        "Entered counting retrieval",
        {"source_hint": source_hint, "collection_name": collection_name},
    )

    # If we have a source hint, get ALL chunks from that source type
    if source_hint:
        print(f"[COUNTING] Retrieving ALL {source_hint} chunks for accurate counting")

        results = collection.get(
            where={"source_type": source_hint},
            include=["documents", "metadatas"]
        )
        _debug_log(
            "H3_H5",
            "src/rag/smart_retriever.py:_counting_retrieval",
            "Collection.get results for source hint",
            {"source_hint": source_hint, "result_count": len(results.get("ids", []))},
        )

        if results["ids"]:
            chunks = []
            for i in range(len(results["ids"])):
                chunk = {
                    "chunk_id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "distance": None,
                }
                chunks.append(chunk)

            print(f"[COUNTING] Retrieved {len(chunks)} chunks from {source_hint} source")
            _debug_log(
                "H3_H5",
                "src/rag/smart_retriever.py:_counting_retrieval",
                "Returning counting chunks from source hint",
                {"source_hint": source_hint, "chunk_count": len(chunks)},
            )
            return chunks
        else:
            # No chunks found - data issue, not retrieval issue
            raise ValueError(
                f"No {source_hint} chunks found in vector store. "
                f"Check data ingestion for source_type='{source_hint}'"
            )

    # source_hint is None - this should have been caught earlier
    raise ValueError(
        f"Cannot perform COUNTING retrieval without source_hint. Query: '{query}'"
    )


def _listing_retrieval(
    query: str,
    openai_api_key: str,
    persist_path: str,
    collection_name: str,
    source_hint: str | None,
) -> list[dict[str, Any]]:
    """Retrieval strategy for listing queries.

    Similar to counting - need comprehensive results.
    """
    collection = get_chroma_collection(persist_path, collection_name)

    if source_hint:
        print(f"[LISTING] Retrieving ALL {source_hint} chunks")

        results = collection.get(
            where={"source_type": source_hint},
            include=["documents", "metadatas"]
        )

        if results["ids"]:
            chunks = []
            for i in range(len(results["ids"])):
                chunk = {
                    "chunk_id": results["ids"][i],
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "distance": None,
                }
                chunks.append(chunk)

            print(f"[LISTING] Retrieved {len(chunks)} chunks")
            return chunks
        else:
            # No chunks found - data issue
            raise ValueError(
                f"No {source_hint} chunks found in vector store for listing query. "
                f"Check data ingestion for source_type='{source_hint}'"
            )

    # source_hint is None - should have been caught earlier
    raise ValueError(
        f"Cannot perform LISTING retrieval without source_hint. Query: '{query}'"
    )


def _semantic_retrieval(
    query: str,
    openai_api_key: str,
    persist_path: str,
    collection_name: str,
) -> list[dict[str, Any]]:
    """Standard semantic retrieval using vector similarity.

    This is the default strategy for most queries.
    """
    print("[SEMANTIC] Using vector similarity search with top_k=10")
    embedder = build_openai_embedder(openai_api_key)
    return search_similar_chunks(
        query, embedder, persist_path, collection_name, top_k=10
    )
