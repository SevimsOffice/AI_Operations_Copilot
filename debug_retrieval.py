"""Debug what chunks are being retrieved for the counting question."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config.config import load_config
from src.rag.retriever import retrieve_context

config = load_config()

query = "How many customer complaints are still open?"

print(f"Query: {query}\n")
print("Retrieving top 5 chunks...\n")

chunks = retrieve_context(
    query=query,
    openai_api_key=config.openai_api_key,
    persist_path=config.chroma_persist_path,
    collection_name=config.collection_name,
    top_k=10
)

print(f"Retrieved {len(chunks)} chunks:\n")

for i, chunk in enumerate(chunks, 1):
    metadata = chunk.get('metadata', {})
    print(f"Chunk {i}:")
    print(f"  Source: {metadata.get('source_file')}")
    print(f"  Type: {metadata.get('source_type')}")
    print(f"  Content preview: {chunk.get('content', '')[:150]}...")
    print()
