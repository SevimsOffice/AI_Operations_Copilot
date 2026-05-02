"""Temporary workaround: Treat .txt files as PDF content for demo purposes."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def ingest_text_as_pdf(text_path: str) -> list[dict[str, Any]]:
    """Read a text file and treat it as PDF content.

    This is a workaround for demo purposes when actual PDFs aren't available.
    """
    text_file = Path(text_path)

    if not text_file.exists():
        raise FileNotFoundError(f"Text file not found: {text_path}")

    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {text_file.name}: {e}")
        return []

    # Split into chunks (roughly 1000 chars each)
    chunk_size = 1000
    chunks = []

    lines = content.split('\n')
    current_chunk = []
    current_length = 0

    for line in lines:
        line_length = len(line)
        if current_length + line_length > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = '\n'.join(current_chunk)
            chunk_id = _generate_chunk_id(text_file.name, len(chunks), chunk_text)

            chunks.append({
                'chunk_id': chunk_id,
                'source_file': text_file.stem + '.pdf',  # Pretend it's a PDF
                'source_type': 'pdf',
                'content': chunk_text,
                'page_number': len(chunks) + 1,
                'metadata': {
                    'file_path': str(text_file),
                    'chunk_index': len(chunks),
                    'char_count': len(chunk_text),
                    'note': 'Converted from text file for demo'
                }
            })

            current_chunk = [line]
            current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length

    # Add remaining chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        chunk_id = _generate_chunk_id(text_file.name, len(chunks), chunk_text)

        chunks.append({
            'chunk_id': chunk_id,
            'source_file': text_file.stem + '.pdf',
            'source_type': 'pdf',
            'content': chunk_text,
            'page_number': len(chunks) + 1,
            'metadata': {
                'file_path': str(text_file),
                'chunk_index': len(chunks),
                'char_count': len(chunk_text),
                'note': 'Converted from text file for demo'
            }
        })

    print(f"[OK] Parsed {text_file.name} as PDF: {len(chunks)} chunks")
    return chunks


def ingest_text_directory_as_pdfs(directory_path: str) -> list[dict[str, Any]]:
    """Ingest all .txt files in a directory as if they were PDFs."""
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Warning: Directory does not exist: {directory_path}")
        return []

    text_files = list(directory.glob("*.txt"))

    if not text_files:
        print(f"No .txt files found in {directory_path}")
        return []

    print(f"\n[PDF-TEXT] Processing {len(text_files)} text files as PDF content from {directory_path}")

    all_chunks = []
    for text_file in text_files:
        try:
            chunks = ingest_text_as_pdf(str(text_file))
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[FAIL] Failed to process {text_file.name}: {e}")
            continue

    print(f"[OK] Total chunks extracted: {len(all_chunks)}\n")
    return all_chunks


def _generate_chunk_id(filename: str, index: int, content: str) -> str:
    """Generate a deterministic unique ID for a chunk."""
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
    return f"pdf_{filename}_{index}_{content_hash}"
