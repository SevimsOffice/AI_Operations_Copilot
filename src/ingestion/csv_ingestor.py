"""CSV ingestion using pandas to produce retrieval-ready chunks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd


def ingest_csv_file(csv_path: str, include_header_context: bool = True) -> list[dict[str, Any]]:
    """Read a CSV file and convert records into chunk dictionaries.

    Args:
        csv_path: Path to the CSV file
        include_header_context: If True, includes column names in chunk content

    Returns:
        List of chunk dictionaries, one per row
    """
    csv_file = Path(csv_path)

    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading {csv_file.name}: {e}")
        return []

    if df.empty:
        print(f"Warning: {csv_file.name} is empty")
        return []

    chunks = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()

        if include_header_context:
            content_parts = [f"{col}: {val}" for col, val in row_dict.items() if pd.notna(val)]
            content = " | ".join(content_parts)
        else:
            content = " | ".join(str(val) for val in row_dict.values() if pd.notna(val))

        if not content.strip():
            continue

        chunk_id = _generate_chunk_id(csv_file.name, idx, content)

        chunk = {
            'chunk_id': chunk_id,
            'source_file': csv_file.name,
            'source_type': 'csv',
            'content': content,
            'row_number': int(idx),
            'metadata': {
                'file_path': str(csv_file),
                'row_index': int(idx),
                'columns': list(df.columns),
                'row_data': row_dict,
                'char_count': len(content)
            }
        }
        chunks.append(chunk)

    print(f"[OK] Parsed {csv_file.name}: {len(chunks)} rows")
    return chunks


def ingest_csv_directory(directory_path: str, include_header_context: bool = True) -> list[dict[str, Any]]:
    """Ingest all CSV files from a directory and aggregate chunks.

    Args:
        directory_path: Path to directory containing CSV files
        include_header_context: If True, includes column names in content

    Returns:
        Aggregated list of all chunks from all CSVs
    """
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Warning: Directory does not exist: {directory_path}")
        return []

    csv_files = list(directory.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {directory_path}")
        return []

    print(f"\n[CSV] Processing {len(csv_files)} CSV files from {directory_path}")

    all_chunks: list[dict[str, Any]] = []
    for csv_file in csv_files:
        try:
            chunks = ingest_csv_file(str(csv_file), include_header_context)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[FAIL] Failed to process {csv_file.name}: {e}")
            continue

    print(f"[OK] Total rows extracted: {len(all_chunks)}\n")
    return all_chunks


def _generate_chunk_id(filename: str, index: int | str, content: str) -> str:
    """Generate a deterministic unique ID for a chunk."""
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
    return f"csv_{filename}_{index}_{content_hash}"
