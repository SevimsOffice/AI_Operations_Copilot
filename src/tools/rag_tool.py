"""RAG tool wrapper used by LangGraph retrieval and answer nodes."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from anthropic import Anthropic

from config.config import load_config
from src.models.schemas import RAGResponse
from src.prompts.rag_prompt import get_rag_system_prompt
from src.rag.retriever import build_citations_from_chunks
from src.rag.smart_retriever import smart_retrieve
from src.execution.validator import validate_rag_response
from src.execution.tracer import tracer


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
    log_path = Path(__file__).resolve().parents[3] / "debug-1129dd.log"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    # endregion


def run_rag_query(
    query: str,
    openai_api_key: str,
    persist_path: str,
    collection_name: str,
    top_k: int = 10,  # Increased from 5 to 10 to get more diverse sources
) -> tuple[list[dict], RAGResponse]:
    """Retrieve context and generate grounded answer with Claude.

    Args:
        query: User's question
        openai_api_key: OpenAI API key for embeddings
        persist_path: ChromaDB persistence path
        collection_name: Collection name
        top_k: Number of chunks to retrieve

    Returns:
        Tuple of (retrieved_chunks, rag_response)
    """
    # Log query start
    tracer.log("query_start", {"query": query[:100]})

    # Step 1: Retrieve relevant chunks using smart retrieval
    chunks = smart_retrieve(
        query=query,
        openai_api_key=openai_api_key,
        persist_path=persist_path,
        collection_name=collection_name,
    )
    source_counts: dict[str, int] = {}
    for chunk in chunks:
        source_type = chunk.get("metadata", {}).get("source_type", "unknown")
        source_counts[source_type] = source_counts.get(source_type, 0) + 1
    _debug_log(
        "H4_H5",
        "src/tools/rag_tool.py:run_rag_query",
        "Retrieved chunks summary before answer generation",
        {"chunk_count": len(chunks), "source_counts": source_counts},
    )

    # Step 2: Build citations
    citations = build_citations_from_chunks(chunks)

    # Step 3: Format context for LLM
    context_text = _format_context_for_llm(chunks)

    # Step 4: Generate answer with Claude
    config = load_config()

    if not chunks:
        # Zero chunks is a system error, not a valid response
        raise ValueError(
            f"Retrieval returned 0 chunks for query: '{query}'. "
            f"This indicates a data ingestion or classification issue."
        )

    try:
        # Log LLM generation start
        tracer.log("llm_generate_start", {
            "chunk_count": len(chunks),
            "model": "claude-sonnet-4-20250514"
        })

        client = Anthropic(api_key=config.anthropic_api_key)

        system_prompt = get_rag_system_prompt()

        # Detect if this is a counting query
        is_counting = any(kw in query.lower() for kw in ["how many", "count", "total number", "number of"])

        counting_reminder = ""
        if is_counting:
            counting_reminder = """\n
**CRITICAL COUNTING INSTRUCTION - FOLLOW EXACTLY:**
1. Go through ALL context blocks labeled "CSV - Individual Records"
2. For each block, check if it matches the criteria (e.g., "status: Open")
3. If it matches, write down the ID (e.g., CMP-2026002)
4. After listing ALL matching IDs, COUNT THEM
5. The count of IDs = your answer
6. VERIFY: Count the number of IDs you listed. That exact number is the answer.
7. DO NOT include any ID with "status: Resolved" when counting "Open" complaints

Example: If you list [CMP-001, CMP-002, CMP-003] then answer = 3, NOT 4 or 2."""

        user_message = f"""Based on the following retrieved context, answer the question.

**Retrieved Context:**
{context_text}

**Question:** {query}{counting_reminder}

Provide a comprehensive answer based strictly on the context above. Cite specific sources when referencing information."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        answer_text = message.content[0].text
        _debug_log(
            "H4",
            "src/tools/rag_tool.py:run_rag_query",
            "Claude answer generated",
            {"answer_preview": answer_text[:300], "chunk_count": len(chunks)},
        )

        # Estimate confidence based on context quality
        confidence = _estimate_confidence(chunks, query)

        response = RAGResponse(
            answer=answer_text,
            citations=citations,
            confidence=confidence,
        )

    except Exception as e:
        print(f"Error generating answer with Claude: {e}")
        response = RAGResponse(
            answer=f"Error generating answer: {str(e)}",
            citations=citations,
            confidence=0.0,
        )

    # VALIDATE before returning
    validate_rag_response(response, chunks)

    # Log query completion
    tracer.log("query_complete", {
        "answer_length": len(response.answer),
        "citation_count": len(response.citations),
        "confidence": response.confidence
    })

    return chunks, response


def _format_context_for_llm(chunks: list[dict]) -> str:
    """Format retrieved chunks into readable context for the LLM.

    Args:
        chunks: Retrieved chunks from vector store

    Returns:
        Formatted context string
    """
    if not chunks:
        return "No relevant context found."

    context_parts = []

    # Add data type clarification
    context_parts.append("IMPORTANT DATA TYPE INFORMATION:")
    context_parts.append("- CSV files contain INDIVIDUAL RECORDS (each row = 1 complaint/item)")
    context_parts.append("- CRM files contain CUSTOMER SUMMARIES with aggregate counts")
    context_parts.append("- When counting, count CSV rows, NOT CRM summary field values\n")

    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get('metadata', {})
        source_file = metadata.get('source_file', 'unknown')
        source_type = metadata.get('source_type', 'unknown')
        content = chunk.get('content', '')

        # Add helpful context based on source type
        if source_type == 'csv':
            header = f"--- Source {i}: {source_file} (CSV - Individual Records) ---"
        elif source_type == 'crm':
            header = f"--- Source {i}: {source_file} (CRM - Customer Summary with Aggregate Fields) ---"
        else:
            header = f"--- Source {i}: {source_file} (type: {source_type}) ---"

        context_parts.append(f"{header}\n{content}\n")

    return "\n".join(context_parts)


def _estimate_confidence(chunks: list[dict], query: str) -> float:
    """Estimate confidence score based on retrieval quality.

    Args:
        chunks: Retrieved chunks
        query: Original query

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if not chunks:
        return 0.0

    # Simple heuristic based on:
    # - Number of chunks retrieved
    # - Average chunk distance (if available)
    # - Query term overlap

    num_chunks = len(chunks)
    if num_chunks == 0:
        return 0.0

    # Base confidence on number of chunks
    base_confidence = min(num_chunks / 5.0, 1.0)

    # Adjust for distance if available
    if 'distance' in chunks[0] and chunks[0]['distance'] is not None:
        avg_distance = sum(c.get('distance', 1.0) for c in chunks) / num_chunks
        # Lower distance = higher confidence (cosine distance)
        # Typical cosine distances range 0-2, with 0 being identical
        distance_factor = max(0, 1.0 - (avg_distance / 2.0))
        confidence = (base_confidence + distance_factor) / 2.0
    else:
        confidence = base_confidence

    return round(confidence, 2)
