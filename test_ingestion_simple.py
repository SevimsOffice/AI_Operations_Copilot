"""Simple test script for CSV and CRM ingestion (no PDF/LlamaParse required)."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.ingestion.csv_ingestor import ingest_csv_directory
from src.ingestion.crm_ingestor import ingest_crm_directory

print("=" * 60)
print("SIMPLE INGESTION TEST - CSV & CRM Only")
print("=" * 60)

# Test CSV ingestion
print("\n1. Testing CSV Ingestion...")
csv_dir = project_root / "data" / "raw_csv"
csv_chunks = ingest_csv_directory(str(csv_dir))

print(f"\n[SUCCESS] CSV Test Complete")
print(f"   Total CSV chunks: {len(csv_chunks)}")
if csv_chunks:
    print(f"   Sample chunk:")
    print(f"     - ID: {csv_chunks[0]['chunk_id']}")
    print(f"     - Source: {csv_chunks[0]['source_file']}")
    print(f"     - Content preview: {csv_chunks[0]['content'][:100]}...")

# Test CRM ingestion
print("\n2. Testing CRM Ingestion...")
crm_dir = project_root / "data" / "mock_crm"
crm_chunks = ingest_crm_directory(str(crm_dir))

print(f"\n[SUCCESS] CRM Test Complete")
print(f"   Total CRM chunks: {len(crm_chunks)}")
if crm_chunks:
    print(f"   Sample chunk:")
    print(f"     - ID: {crm_chunks[0]['chunk_id']}")
    print(f"     - Source: {crm_chunks[0]['source_file']}")
    print(f"     - Content preview: {crm_chunks[0]['content'][:100]}...")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"[OK] CSV chunks: {len(csv_chunks)}")
print(f"[OK] CRM chunks: {len(crm_chunks)}")
print(f"[OK] Total chunks: {len(csv_chunks) + len(crm_chunks)}")
print("\n[SUCCESS] Data ingestion working! Next: Install remaining packages for full pipeline.")
