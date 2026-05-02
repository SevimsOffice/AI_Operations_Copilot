"""Validation layer for deterministic query execution."""

from typing import Any
from src.rag.query_classifier import QueryType


def validate_retrieval_result(
    query: str,
    query_type: QueryType,
    source_hint: str | None,
    chunks: list[dict[str, Any]]
) -> None:
    """Validate that retrieval results match expected contract.

    Raises:
        ValueError: If retrieval violates deterministic contract
    """
    # Rule 1: Must retrieve at least 1 chunk
    if len(chunks) == 0:
        raise ValueError(
            f"Retrieved 0 chunks for query_type={query_type.value}, "
            f"source_hint={source_hint}, query='{query[:100]}'"
        )

    # Rule 2: Counting queries must retrieve ONLY CSV chunks
    if query_type == QueryType.COUNTING:
        source_types = {c.get('metadata', {}).get('source_type') for c in chunks}
        if source_types != {'csv'}:
            raise ValueError(
                f"COUNTING query retrieved mixed sources: {source_types}. "
                f"Expected only 'csv'. Query: '{query}'"
            )

        # Rule 3: Must retrieve ALL CSV chunks for counting accuracy
        # (This should be validated by comparing len(chunks) to total CSV count)

    # Rule 4: All chunks must have valid metadata
    for i, chunk in enumerate(chunks):
        if 'metadata' not in chunk:
            raise ValueError(f"Chunk {i} missing 'metadata' field")
        if 'source_type' not in chunk['metadata']:
            raise ValueError(f"Chunk {i} missing 'metadata.source_type'")


def validate_rag_response(
    rag_response: Any,
    chunks: list[dict[str, Any]]
) -> None:
    """Validate RAG response structure.

    Raises:
        ValueError: If response violates contract
    """
    if rag_response is None:
        raise ValueError("RAG response is None")

    if not hasattr(rag_response, 'answer'):
        raise ValueError("RAG response missing 'answer' field")

    if not rag_response.answer or len(rag_response.answer.strip()) == 0:
        raise ValueError("RAG response has empty answer")

    if not hasattr(rag_response, 'citations'):
        raise ValueError("RAG response missing 'citations' field")

    if not hasattr(rag_response, 'confidence'):
        raise ValueError("RAG response missing 'confidence' field")
