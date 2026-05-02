"""Shared helper functions used across ingestion, retrieval, and UI layers."""

from __future__ import annotations

from typing import Iterable, TypeVar

T = TypeVar("T")


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace for chunking and display consistency."""
    return " ".join(text.split())


def flatten_list(nested_items: Iterable[list[T]]) -> list[T]:
    """Flatten a list of lists into a single list."""
    # Architecture note: utility helpers avoid duplicating small data transforms.
    flattened: list[T] = []
    for items in nested_items:
        flattened.extend(items)
    return flattened
