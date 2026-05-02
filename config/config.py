"""Centralized environment-driven configuration for Atlas Operations Copilot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """Typed configuration loaded from environment variables."""

    anthropic_api_key: str
    openai_api_key: str
    llama_cloud_api_key: str
    chroma_persist_path: str
    collection_name: str
    project_root: Path


def load_config() -> AppConfig:
    """Load all runtime configuration from `.env` or process env."""
    # Architecture note: a single config object keeps dependency wiring explicit.
    load_dotenv()
    project_root = Path(__file__).resolve().parents[1]
    return AppConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        llama_cloud_api_key=os.getenv("LLAMA_CLOUD_API_KEY", ""),
        chroma_persist_path=os.getenv("CHROMA_PERSIST_PATH", "./data/chroma_db"),
        collection_name=os.getenv("COLLECTION_NAME", "atlas_operations"),
        project_root=project_root,
    )
