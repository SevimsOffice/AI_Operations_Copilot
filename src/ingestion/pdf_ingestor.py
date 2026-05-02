"""PDF ingestion using LlamaParse to produce retrieval-ready chunks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from llama_parse import LlamaParse


def ingest_pdf_file(pdf_path: str, llama_cloud_api_key: str) -> list[dict[str, Any]]:
    """Parse a single PDF and return normalized chunk dictionaries.

    Args:
        pdf_path: Path to the PDF file
        llama_cloud_api_key: API key for LlamaParse cloud service

    Returns:
        List of chunk dictionaries with structure:
        {
            'chunk_id': str,
            'source_file': str,
            'source_type': 'pdf',
            'content': str,
            'page_number': int | None,
            'metadata': dict
        }
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    parser = LlamaParse(
        api_key=llama_cloud_api_key,
        result_type="markdown",
        verbose=True,
        language="en"
    )

    try:
        documents = parser.load_data(str(pdf_file))
    except Exception as e:
        print(f"Error parsing {pdf_file.name}: {e}")
        return []

    chunks = []
    for idx, doc in enumerate(documents):
        content = doc.text.strip()
        if not content:
            continue

        chunk_id = _generate_chunk_id(pdf_file.name, idx, content)

        chunk = {
            'chunk_id': chunk_id,
            'source_file': pdf_file.name,
            'source_type': 'pdf',
            'content': content,
            'page_number': doc.metadata.get('page_number'),
            'metadata': {
                'file_path': str(pdf_file),
                'chunk_index': idx,
                'char_count': len(content),
                **doc.metadata
            }
        }
        chunks.append(chunk)

    print(f"[OK] Parsed {pdf_file.name}: {len(chunks)} chunks")
    return chunks


def ingest_pdf_directory(directory_path: str, llama_cloud_api_key: str) -> list[dict[str, Any]]:
    """Ingest all PDFs in a directory and aggregate chunks.

    Args:
        directory_path: Path to directory containing PDF files
        llama_cloud_api_key: API key for LlamaParse

    Returns:
        Aggregated list of all chunks from all PDFs
    """
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Warning: Directory does not exist: {directory_path}")
        return []

    pdf_files = list(directory.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return []

    print(f"\n[PDF] Processing {len(pdf_files)} PDF files from {directory_path}")

    all_chunks: list[dict[str, Any]] = []
    for pdf_file in pdf_files:
        try:
            chunks = ingest_pdf_file(str(pdf_file), llama_cloud_api_key)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[FAIL] Failed to process {pdf_file.name}: {e}")
            continue

    print(f"[OK] Total chunks extracted: {len(all_chunks)}\n")
    return all_chunks


def _generate_chunk_id(filename: str, index: int, content: str) -> str:
    """Generate a deterministic unique ID for a chunk."""
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
    return f"pdf_{filename}_{index}_{content_hash}"
