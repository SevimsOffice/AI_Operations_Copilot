"""Pydantic v2 schema definitions for structured copilot outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    """Citation payload describing a supporting source snippet."""

    source_file: str
    source_type: Literal["pdf", "csv", "crm"]
    relevant_excerpt: str


class RAGResponse(BaseModel):
    """Primary answer model returned from retrieval-grounded generation."""

    answer: str
    citations: list[SourceCitation]
    confidence: float = Field(ge=0.0, le=1.0)


class OperationalInsight(BaseModel):
    """Single structured operational insight extracted from retrieved data."""

    category: Literal["bottleneck", "risk", "opportunity", "action"]
    title: str
    description: str
    severity: Literal["high", "medium", "low"]
    affected_area: str
    source_references: list[str]
    recommended_action: str


class AnalysisReport(BaseModel):
    """Structured report aggregating operational insights for a query."""

    query: str
    insights: list[OperationalInsight]
    summary: str
    data_sources_used: list[str]
    generated_at: str
