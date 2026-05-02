"""System prompt template for structured operational analysis."""

from __future__ import annotations

# Moved to rag_prompt.py to consolidate prompts
from src.prompts.rag_prompt import get_analysis_system_prompt

__all__ = ['get_analysis_system_prompt']
