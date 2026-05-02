"""Mock CRM JSON ingestion to produce retrieval-ready chunks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def ingest_crm_file(json_path: str) -> list[dict[str, Any]]:
    """Read a CRM JSON file and convert entities into chunk dictionaries.

    Args:
        json_path: Path to the CRM JSON file

    Returns:
        List of chunk dictionaries, one per CRM record

    Notes:
        Expects JSON to be either:
        - A list of objects: [{...}, {...}]
        - An object with a records key: {"records": [...]}
        - A single object: {...} (will be wrapped in a list)
    """
    json_file = Path(json_path)

    if not json_file.exists():
        raise FileNotFoundError(f"CRM JSON file not found: {json_path}")

    try:
        with json_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_file.name}: {e}")
        return []

    records = _normalize_crm_data(data)

    if not records:
        print(f"Warning: No records found in {json_file.name}")
        return []

    chunks = []
    for idx, record in enumerate(records):
        content = _flatten_crm_record(record)

        if not content.strip():
            continue

        chunk_id = _generate_chunk_id(json_file.name, idx, content)

        chunk = {
            'chunk_id': chunk_id,
            'source_file': json_file.name,
            'source_type': 'crm',
            'content': content,
            'record_index': idx,
            'metadata': {
                'file_path': str(json_file),
                'record_index': idx,
                'record_data': record,
                'char_count': len(content)
            }
        }
        chunks.append(chunk)

    print(f"[OK] Parsed {json_file.name}: {len(chunks)} records")
    return chunks


def ingest_crm_directory(directory_path: str) -> list[dict[str, Any]]:
    """Ingest all CRM JSON files in a directory and aggregate chunks.

    Args:
        directory_path: Path to directory containing CRM JSON files

    Returns:
        Aggregated list of all chunks from all CRM files
    """
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Warning: Directory does not exist: {directory_path}")
        return []

    json_files = list(directory.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {directory_path}")
        return []

    print(f"\n[CRM] Processing {len(json_files)} CRM JSON files from {directory_path}")

    all_chunks: list[dict[str, Any]] = []
    for json_file in json_files:
        try:
            chunks = ingest_crm_file(str(json_file))
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[FAIL] Failed to process {json_file.name}: {e}")
            continue

    print(f"[OK] Total records extracted: {len(all_chunks)}\n")
    return all_chunks


def _normalize_crm_data(data: Any) -> list[dict[str, Any]]:
    """Normalize various CRM JSON structures into a list of records."""
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "records" in data:
            return data["records"]
        elif "data" in data:
            return data["data"]
        else:
            return [data]
    else:
        return []


def _flatten_crm_record(record: dict[str, Any], prefix: str = "") -> str:
    """Flatten a nested CRM record into a readable text representation."""
    parts = []

    for key, value in record.items():
        full_key = f"{prefix}{key}" if prefix else key

        if isinstance(value, dict):
            nested = _flatten_crm_record(value, f"{full_key}.")
            if nested:
                parts.append(nested)
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                for i, item in enumerate(value):
                    nested = _flatten_crm_record(item, f"{full_key}[{i}].")
                    if nested:
                        parts.append(nested)
            else:
                parts.append(f"{full_key}: {', '.join(str(v) for v in value)}")
        elif value is not None and str(value).strip():
            parts.append(f"{full_key}: {value}")

    return " | ".join(parts)


def _generate_chunk_id(filename: str, index: int, content: str) -> str:
    """Generate a deterministic unique ID for a chunk."""
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
    return f"crm_{filename}_{index}_{content_hash}"
