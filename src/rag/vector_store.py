"""ChromaDB vector store setup with local persistence."""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from src.rag.embedder import embed_query, embed_texts


def get_chroma_collection(persist_path: str, collection_name: str) -> Any:
    """Initialize or return an existing ChromaDB collection.

    Args:
        persist_path: Path to ChromaDB persistence directory
        collection_name: Name of the collection

    Returns:
        ChromaDB collection instance
    """
    client = chromadb.PersistentClient(
        path=persist_path,
        settings=Settings(anonymized_telemetry=False)
    )
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def upsert_chunks(
    chunks: list[dict[str, Any]],
    embedder: OpenAI,
    persist_path: str,
    collection_name: str,
    batch_size: int = 100,
) -> None:
    """Upsert chunk payloads and vectors into persistent ChromaDB.

    Args:
        chunks: List of chunk dictionaries with 'chunk_id', 'content', etc.
        embedder: OpenAI client for generating embeddings
        persist_path: Path to ChromaDB persistence directory
        collection_name: Name of the collection
        batch_size: Number of chunks to process per batch
    """
    if not chunks:
        print("No chunks to upsert")
        return

    collection = get_chroma_collection(persist_path, collection_name)

    print(f"\n[PROCESSING] Embedding and upserting {len(chunks)} chunks...")

    texts = [chunk['content'] for chunk in chunks]
    embeddings = embed_texts(embedder, texts)

    if len(embeddings) != len(chunks):
        raise ValueError(f"Embedding count ({len(embeddings)}) doesn't match chunk count ({len(chunks)})")

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]

        ids = [chunk['chunk_id'] for chunk in batch_chunks]
        documents = [chunk['content'] for chunk in batch_chunks]
        metadatas = [
            {
                'source_file': chunk['source_file'],
                'source_type': chunk['source_type'],
                **{k: v for k, v in chunk.get('metadata', {}).items()
                   if isinstance(v, (str, int, float, bool))}
            }
            for chunk in batch_chunks
        ]

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=batch_embeddings,
                metadatas=metadatas
            )
            print(f"  [OK] Upserted batch {i // batch_size + 1} ({len(batch_chunks)} chunks)")
        except Exception as e:
            print(f"  [FAIL] Error upserting batch at index {i}: {e}")

    print(f"[OK] Total chunks in collection: {collection.count()}\n")


def search_similar_chunks(
    query: str,
    embedder: OpenAI,
    persist_path: str,
    collection_name: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve top-k similar chunks from ChromaDB for a query.

    Args:
        query: Query text to search for
        embedder: OpenAI client for generating query embedding
        persist_path: Path to ChromaDB persistence directory
        collection_name: Name of the collection
        top_k: Number of results to return

    Returns:
        List of chunk dictionaries with similarity scores
    """
    if not query.strip():
        return []

    collection = get_chroma_collection(persist_path, collection_name)

    if collection.count() == 0:
        print("Warning: Collection is empty. Run ingestion first.")
        return []

    query_embedding = embed_query(embedder, query)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count())
        )
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []

    if not results['ids'] or not results['ids'][0]:
        return []

    chunks = []
    for i in range(len(results['ids'][0])):
        chunk = {
            'chunk_id': results['ids'][0][i],
            'content': results['documents'][0][i],
            'metadata': results['metadatas'][0][i],
            'distance': results['distances'][0][i] if 'distances' in results else None,
        }
        chunks.append(chunk)

    return chunks
