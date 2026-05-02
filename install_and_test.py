"""Complete installation and testing script for Atlas Operations Copilot."""

import subprocess
import sys
from pathlib import Path

print("=" * 70)
print("ATLAS OPERATIONS COPILOT - Installation & Setup")
print("=" * 70)

# Step 1: Install dependencies
print("\n[1/4] Installing Python dependencies...")
print("This may take 3-5 minutes...\n")

try:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "anthropic", "openai", "chromadb", "pandas", "python-dotenv",
        "langgraph", "langchain-core", "langchain-anthropic", "langchain-openai",
        "streamlit", "pydantic>=2.0",
        "--quiet"
    ])
    print("[OK] Dependencies installed successfully!")
except subprocess.CalledProcessError as e:
    print(f"[FAIL] Error installing dependencies: {e}")
    sys.exit(1)

# Step 2: Verify imports
print("\n[2/4] Verifying package imports...")

try:
    import anthropic
    import openai
    import chromadb
    import pandas
    import streamlit
    import langgraph
    from pydantic import BaseModel

    print("[OK] All core packages imported successfully!")
except ImportError as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Step 3: Check data files
print("\n[3/4] Checking data files...")

project_root = Path(__file__).parent
data_files = {
    "CSV": project_root / "data" / "raw_csv" / "customer_complaints.csv",
    "CRM": project_root / "data" / "mock_crm" / "crm_mock_dataset.json",
}

all_exist = True
for name, path in data_files.items():
    if path.exists():
        print(f"[OK] {name} data file found: {path.name}")
    else:
        print(f"[WARN] {name} data file missing: {path}")
        all_exist = False

if not all_exist:
    print("\n[WARN] Some data files are missing. You can still run the system,")
    print("       but you'll have limited data to query.")

# Step 4: Check API keys
print("\n[4/4] Checking API keys...")

from dotenv import load_dotenv
import os

load_dotenv()

api_keys = {
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
}

keys_configured = True
for key_name, key_value in api_keys.items():
    if key_value and key_value != "your_key_here":
        print(f"[OK] {key_name} configured")
    else:
        print(f"[FAIL] {key_name} not configured in .env")
        keys_configured = False

print("\n" + "=" * 70)
print("SETUP COMPLETE!")
print("=" * 70)

if keys_configured and all_exist:
    print("\n[SUCCESS] Your system is fully configured and ready to use!")
    print("\nNext steps:")
    print("  1. Test data ingestion:")
    print("     python test_simple_query.py")
    print("\n  2. Run the Streamlit UI:")
    print("     streamlit run ui/streamlit_app.py")
    print("\n  3. Or run full ingestion pipeline:")
    print("     python scripts/ingest_all.py")

elif not keys_configured:
    print("\n[ACTION REQUIRED] Configure your API keys in the .env file:")
    print("  - ANTHROPIC_API_KEY (for Claude)")
    print("  - OPENAI_API_KEY (for embeddings)")
    print("\nThen run this script again.")

else:
    print("\n[ACTION REQUIRED] Add data files to test the system:")
    print("  - data/raw_csv/ (CSV files)")
    print("  - data/mock_crm/ (JSON files)")
    print("\nYou can still test with existing data.")

print("\n" + "=" * 70)
