"""Retriever module for semantic search and source citation assembly."""

from __future__ import annotations

from typing import Any

from src.models.schemas import SourceCitation
from src.rag.embedder import build_openai_embedder
from src.rag.vector_store import search_similar_chunks


def retrieve_context(
    query: str,
    openai_api_key: str,
    persist_path: str,
    collection_name: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve top-k relevant chunks for a user query."""
    # Architecture note: retriever is isolated from agent orchestration for reuse.
    embedder = build_openai_embedder(openai_api_key)
    return search_similar_chunks(
        query=query,
        embedder=embedder,
        persist_path=persist_path,
        collection_name=collection_name,
        top_k=top_k,
    )


def build_citations_from_chunks(chunks: list[dict[str, Any]], max_excerpt_length: int = 200) -> list[SourceCitation]:
    """Build typed citation models from retrieved chunk metadata.

    Args:
        chunks: Retrieved chunks from vector store
        max_excerpt_length: Maximum character length for excerpts

    Returns:
        List of SourceCitation objects (deduplicated by source)
    """
    # Group chunks by source file to avoid duplicate citations
    sources_seen = {}

    for chunk in chunks:
        metadata = chunk.get('metadata', {})
        content = chunk.get('content', '')

        source_file = metadata.get('source_file', 'unknown')
        source_type = metadata.get('source_type', 'pdf')

        # Create a unique key for this source
        source_key = f"{source_file}:{source_type}"

        # If we haven't seen this source, add it
        if source_key not in sources_seen:
            excerpt = content[:max_excerpt_length]
            if len(content) > max_excerpt_length:
                excerpt += "..."

            # For CSV/CRM, show how many records from this source
            source_display = source_file

            sources_seen[source_key] = {
                'source_file': source_display,
                'source_type': source_type,
                'excerpt': excerpt,
                'count': 1
            }
        else:
            # Increment count for this source
            sources_seen[source_key]['count'] += 1

    # Build citation objects
    citations = []
    for source_info in sources_seen.values():
        # Show count if multiple chunks from same source
        source_display = source_info['source_file']
        if source_info['count'] > 1:
            source_display += f" ({source_info['count']} records)"

        citation = SourceCitation(
            source_file=source_display,
            source_type=source_info['source_type'],
            relevant_excerpt=source_info['excerpt']
        )
        citations.append(citation)

    return citations
