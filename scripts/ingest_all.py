"""Batch ingestion script for all Atlas Operations Copilot data sources."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.config import load_config
from src.ingestion.crm_ingestor import ingest_crm_directory
from src.ingestion.csv_ingestor import ingest_csv_directory
from src.ingestion.pdf_ingestor import ingest_pdf_directory
from src.rag.embedder import build_openai_embedder
from src.rag.vector_store import upsert_chunks


def run_full_ingestion() -> None:
    """Ingest PDFs, CSVs, and CRM JSON, then index all chunks in ChromaDB."""
    print("=" * 60)
    print("Atlas Operations Copilot - Data Ingestion Pipeline")
    print("=" * 60)

    config = load_config()

    missing = []
    if not config.llama_cloud_api_key:
        missing.append("LLAMA_CLOUD_API_KEY")
    if not config.openai_api_key:
        missing.append("OPENAI_API_KEY")

    if missing:
        print(f"\n[FAIL] Missing required API keys: {', '.join(missing)}")
        print("Please configure these in your .env file")
        return

    data_root = config.project_root / "data"

    pdf_dir = data_root / "raw_pdfs"
    csv_dir = data_root / "raw_csv"
    crm_dir = data_root / "mock_crm"

    pdf_chunks = ingest_pdf_directory(str(pdf_dir), config.llama_cloud_api_key)
    csv_chunks = ingest_csv_directory(str(csv_dir))
    crm_chunks = ingest_crm_directory(str(crm_dir))

    all_chunks = pdf_chunks + csv_chunks + crm_chunks

    if not all_chunks:
        print("\n[WARN]  No data found to ingest.")
        print("Please add files to:")
        print(f"  - {pdf_dir}")
        print(f"  - {csv_dir}")
        print(f"  - {crm_dir}")
        return

    print(f"\n[DATA] Total chunks collected: {len(all_chunks)}")
    print(f"  • PDF chunks: {len(pdf_chunks)}")
    print(f"  • CSV chunks: {len(csv_chunks)}")
    print(f"  • CRM chunks: {len(crm_chunks)}")

    embedder = build_openai_embedder(config.openai_api_key)

    upsert_chunks(
        chunks=all_chunks,
        embedder=embedder,
        persist_path=config.chroma_persist_path,
        collection_name=config.collection_name,
    )

    print("=" * 60)
    print("[OK] Ingestion complete!")
    print("=" * 60)
    print(f"\nVector store persisted to: {config.chroma_persist_path}")
    print(f"Collection name: {config.collection_name}")
    print("\nYou can now run the Streamlit app:")
    print("  streamlit run ui/streamlit_app.py")


if __name__ == "__main__":
    run_full_ingestion()
