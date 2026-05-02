"""Simple end-to-end test without PDF ingestion (uses existing CSV/CRM data)."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("SIMPLE QUERY TEST - Without Full Ingestion")
print("=" * 70)

print("\n[INFO] This test:")
print("  1. Ingests CSV and CRM data (no PDFs)")
print("  2. Creates embeddings with OpenAI")
print("  3. Stores in ChromaDB")
print("  4. Runs a sample query through the LangGraph agent")
print("  5. Shows the answer with citations")

# Step 1: Quick ingestion
print("\n" + "=" * 70)
print("STEP 1: Data Ingestion")
print("=" * 70)

from config.config import load_config
from src.ingestion.csv_ingestor import ingest_csv_directory
from src.ingestion.crm_ingestor import ingest_crm_directory
from src.rag.embedder import build_openai_embedder
from src.rag.vector_store import upsert_chunks

config = load_config()

# Check API keys
if not config.openai_api_key or config.openai_api_key == "your_key_here":
    print("\n[FAIL] OPENAI_API_KEY not configured in .env")
    print("Please add your OpenAI API key to the .env file")
    sys.exit(1)

if not config.anthropic_api_key or config.anthropic_api_key == "your_key_here":
    print("\n[FAIL] ANTHROPIC_API_KEY not configured in .env")
    print("Please add your Anthropic API key to the .env file")
    sys.exit(1)

print("\n[1/3] Ingesting CSV files...")
csv_dir = config.project_root / "data" / "raw_csv"
csv_chunks = ingest_csv_directory(str(csv_dir))

print("\n[2/3] Ingesting CRM files...")
crm_dir = config.project_root / "data" / "mock_crm"
crm_chunks = ingest_crm_directory(str(crm_dir))

all_chunks = csv_chunks + crm_chunks

if not all_chunks:
    print("\n[FAIL] No data found to ingest")
    print("Please add files to data/raw_csv/ and data/mock_crm/")
    sys.exit(1)

print(f"\n[3/3] Creating embeddings and storing in ChromaDB...")
print(f"  Total chunks: {len(all_chunks)}")

embedder = build_openai_embedder(config.openai_api_key)

upsert_chunks(
    chunks=all_chunks,
    embedder=embedder,
    persist_path=config.chroma_persist_path,
    collection_name=config.collection_name,
)

print("\n[SUCCESS] Data ingestion complete!")

# Step 2: Test query
print("\n" + "=" * 70)
print("STEP 2: Test Query")
print("=" * 70)

test_queries = [
    "What are the most common customer complaints?",
    "Which customers have open complaints?",
    "Analyze the top operational risks",
]

print("\nAvailable test queries:")
for i, query in enumerate(test_queries, 1):
    print(f"  {i}. {query}")

print("\nRunning query 1...")
query = test_queries[0]

print(f"\n[QUERY] {query}")
print("\n[PROCESSING] Running through LangGraph agent...")

from src.agents.graph import build_copilot_graph

try:
    graph = build_copilot_graph()

    initial_state = {
        "query": query,
        "retrieved_chunks": [],
        "rag_response": None,
        "analysis_report": None,
        "error": None,
    }

    result = graph.invoke(initial_state)

    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    if result.get("error"):
        print(f"\n[FAIL] Error: {result['error']}")
    elif result.get("rag_response"):
        rag_response = result["rag_response"]

        print(f"\n[ANSWER]")
        print(rag_response.answer)

        print(f"\n[CONFIDENCE] {int(rag_response.confidence * 100)}%")

        print(f"\n[CITATIONS] {len(rag_response.citations)} sources")
        for i, citation in enumerate(rag_response.citations, 1):
            print(f"  {i}. {citation.source_file} ({citation.source_type})")

        if result.get("analysis_report"):
            print(f"\n[ANALYSIS REPORT]")
            report = result["analysis_report"]
            print(f"Insights: {len(report.insights)}")
            for insight in report.insights:
                print(f"  - [{insight.severity.upper()}] {insight.title}")

    else:
        print("\n[WARN] No response generated")

    print("\n" + "=" * 70)
    print("[SUCCESS] Test complete!")
    print("=" * 70)

    print("\nNext steps:")
    print("  1. Run the Streamlit UI:")
    print("     streamlit run ui/streamlit_app.py")
    print("\n  2. Try other test queries by modifying this script")
    print("\n  3. Add PDF files and run full ingestion:")
    print("     python scripts/ingest_all.py")

except Exception as e:
    print(f"\n[FAIL] Error running query: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
