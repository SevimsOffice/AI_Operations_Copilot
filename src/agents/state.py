"""State schema for the LangGraph Atlas Operations Copilot workflow."""

from __future__ import annotations

from typing import Optional, TypedDict

from src.models.schemas import AnalysisReport, RAGResponse, SourceCitation


class CopilotState(TypedDict, total=False):
    """State container passed between LangGraph nodes.

    Attributes:
        query: User's input question
        retrieved_chunks: Raw chunks from vector search
        rag_response: Structured RAG response with citations
        analysis_report: Structured operational insights (optional)
        error: Error message if something fails
        context_text: Formatted context for LLM
        answer_text: Final text answer
        citations: List of source citations
    """

    query: str
    retrieved_chunks: list[dict]
    rag_response: Optional[RAGResponse]
    analysis_report: Optional[AnalysisReport]
    error: Optional[str]
    context_text: Optional[str]
    answer_text: Optional[str]
    citations: list[SourceCitation]
