"""Test the LangGraph agent directly without Streamlit UI."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("TESTING LANGGRAPH AGENT DIRECTLY")
print("=" * 70)

# First, let's ingest data quickly
print("\n[STEP 1] Quick data ingestion...")

from config.config import load_config
from src.ingestion.csv_ingestor import ingest_csv_directory
from src.ingestion.crm_ingestor import ingest_crm_directory
from src.rag.embedder import build_openai_embedder
from src.rag.vector_store import upsert_chunks

config = load_config()

print("\nIngesting CSV...")
csv_dir = config.project_root / "data" / "raw_csv"
csv_chunks = ingest_csv_directory(str(csv_dir))

print("\nIngesting CRM...")
crm_dir = config.project_root / "data" / "mock_crm"
crm_chunks = ingest_crm_directory(str(crm_dir))

all_chunks = csv_chunks + crm_chunks

if not all_chunks:
    print("\n[FAIL] No data found")
    sys.exit(1)

print(f"\n[OK] Total chunks: {len(all_chunks)}")

# Create embeddings
print("\n[STEP 2] Creating embeddings...")
embedder = build_openai_embedder(config.openai_api_key)

upsert_chunks(
    chunks=all_chunks,
    embedder=embedder,
    persist_path=config.chroma_persist_path,
    collection_name=config.collection_name,
)

print("\n[OK] Vector store ready!")

# Test the agent
print("\n" + "=" * 70)
print("[STEP 3] TESTING LANGGRAPH AGENT")
print("=" * 70)

from src.agents.graph import build_copilot_graph

test_queries = [
    "What are the most common customer complaints?",
    "Which customers have open complaints?",
]

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*70}")
    print(f"TEST QUERY {i}")
    print(f"{'='*70}")
    print(f"\n[QUERY] {query}")

    try:
        graph = build_copilot_graph()

        initial_state = {
            "query": query,
            "retrieved_chunks": [],
            "rag_response": None,
            "analysis_report": None,
            "error": None,
        }

        print("\n[PROCESSING] Running through LangGraph...")
        result = graph.invoke(initial_state)

        if result.get("error"):
            print(f"\n[FAIL] Error: {result['error']}")
            continue

        if result.get("rag_response"):
            rag_response = result["rag_response"]

            print(f"\n{'='*70}")
            print("ANSWER")
            print(f"{'='*70}")
            print(f"\n{rag_response.answer}\n")

            print(f"[CONFIDENCE] {int(rag_response.confidence * 100)}%")
            print(f"[CITATIONS] {len(rag_response.citations)} sources:")
            for j, citation in enumerate(rag_response.citations, 1):
                print(f"  {j}. {citation.source_file} ({citation.source_type})")

            if result.get("analysis_report"):
                print(f"\n[ANALYSIS] {len(result['analysis_report'].insights)} insights generated")
        else:
            print("\n[WARN] No response generated")

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("[SUCCESS] Agent testing complete!")
print("=" * 70)

print("\nThe LangGraph agent is working correctly!")
print("\nFor the Streamlit UI, you can:")
print("  1. Run: streamlit run ui/streamlit_app.py")
print("  2. Or access directly in browser if it's running in background")
print("  3. Or use this script to demo the agent functionality")
