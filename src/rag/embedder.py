"""Embedding helpers using OpenAI text-embedding-3-small."""

from __future__ import annotations

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 100


def build_openai_embedder(openai_api_key: str) -> OpenAI:
    """Construct an OpenAI client for embedding generation.

    Args:
        openai_api_key: OpenAI API key

    Returns:
        Configured OpenAI client
    """
    return OpenAI(api_key=openai_api_key)


def embed_texts(embedder: OpenAI, texts: list[str], model: str = EMBEDDING_MODEL) -> list[list[float]]:
    """Embed a list of texts with OpenAI embedding model.

    Args:
        embedder: OpenAI client instance
        texts: List of text strings to embed
        model: Embedding model name (default: text-embedding-3-small)

    Returns:
        List of embedding vectors (list of floats per text)

    Notes:
        Processes in batches to avoid rate limits
    """
    if not texts:
        return []

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]

        try:
            response = embedder.embeddings.create(
                input=batch,
                model=model
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            print(f"  [OK] Embedded batch {i // EMBEDDING_BATCH_SIZE + 1} ({len(batch)} texts)")

        except Exception as e:
            print(f"  [FAIL] Error embedding batch starting at index {i}: {e}")
            all_embeddings.extend([[0.0] * 1536] * len(batch))

    return all_embeddings


def embed_query(embedder: OpenAI, query: str, model: str = EMBEDDING_MODEL) -> list[float]:
    """Embed a single query string for vector retrieval.

    Args:
        embedder: OpenAI client instance
        query: Query text to embed
        model: Embedding model name (default: text-embedding-3-small)

    Returns:
        Single embedding vector (list of floats)
    """
    if not query.strip():
        return [0.0] * 1536

    try:
        response = embedder.embeddings.create(
            input=[query],
            model=model
        )
        return response.data[0].embedding

    except Exception as e:
        print(f"Error embedding query: {e}")
        return [0.0] * 1536
