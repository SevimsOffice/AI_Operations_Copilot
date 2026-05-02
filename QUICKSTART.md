# 🚀 Quick Start Guide - Atlas Operations Copilot

## Current Status: 60% Complete ✅

**What's implemented:**
- ✅ Complete data ingestion pipeline (PDF, CSV, CRM)
- ✅ OpenAI embeddings + ChromaDB vector store
- ✅ Pydantic models for structured output

**What's pending:**
- ⏳ LangGraph agent workflow (3 files to implement)
- ⏳ Streamlit chat interface
- ⏳ Claude API integration

---

## 📋 Prerequisites

Before you start, make sure you have:

1. **Python 3.11+** installed
2. **API Keys** for:
   - Anthropic (Claude)
   - OpenAI (embeddings)
   - LlamaCloud (PDF parsing)

---

## 🏁 Step-by-Step Setup

### 1. Navigate to Project

```bash
cd "C:\Users\Administrator\Desktop\Project 3004\atlas-operations-copilot"
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Expected packages:
- `anthropic` - Claude API
- `openai` - Embeddings
- `langgraph` - Agent orchestration
- `chromadb` - Vector store
- `llama-parse` - PDF parsing
- `streamlit` - UI
- `pydantic>=2.0` - Data models

### 4. Configure API Keys

Copy the example environment file:

```bash
copy .env.example .env  # Windows
```

Edit `.env` and add your real API keys:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
LLAMA_CLOUD_API_KEY=llx-...
CHROMA_PERSIST_PATH=./data/chroma_db
COLLECTION_NAME=atlas_operations
```

### 5. Add Sample Data

Place your files in these folders:

```
data/
├── raw_pdfs/       ← Add .pdf files here
├── raw_csv/        ← Add .csv files here
└── mock_crm/       ← Add .json files here (CRM records)
```

**Sample CRM JSON structure:**

```json
{
  "records": [
    {
      "account_id": "ACC-001",
      "company_name": "Acme Corp",
      "status": "active",
      "revenue": 125000,
      "notes": "High-priority customer"
    }
  ]
}
```

Or just a list:

```json
[
  {
    "id": 1,
    "customer": "Widget Inc",
    "deal_stage": "negotiation"
  }
]
```

### 6. Run Data Ingestion

This will parse all your files, create embeddings, and store them in ChromaDB:

```bash
python scripts/ingest_all.py
```

**Expected output:**

```
============================================================
Atlas Operations Copilot - Data Ingestion Pipeline
============================================================

📄 Processing 3 PDF files from data/raw_pdfs
✓ Parsed playbook.pdf: 45 chunks
✓ Parsed sop_v2.pdf: 23 chunks
✓ Parsed report_q1.pdf: 67 chunks
✓ Total chunks extracted: 135

📊 Processing 2 CSV files from data/raw_csv
✓ Parsed inventory.csv: 120 rows
✓ Parsed metrics.csv: 84 rows
✓ Total rows extracted: 204

🗂️  Processing 1 CRM JSON files from data/mock_crm
✓ Parsed accounts.json: 15 records
✓ Total records extracted: 15

📊 Total chunks collected: 354
  • PDF chunks: 135
  • CSV chunks: 204
  • CRM chunks: 15

🔄 Embedding and upserting 354 chunks...
  ✓ Embedded batch 1 (100 texts)
  ✓ Embedded batch 2 (100 texts)
  ✓ Embedded batch 3 (100 texts)
  ✓ Embedded batch 4 (54 texts)
  ✓ Upserted batch 1 (100 chunks)
  ✓ Upserted batch 2 (100 chunks)
  ✓ Upserted batch 3 (100 chunks)
  ✓ Upserted batch 4 (54 chunks)
✓ Total chunks in collection: 354

============================================================
✅ Ingestion complete!
============================================================

Vector store persisted to: ./data/chroma_db
Collection name: atlas_operations

You can now run the Streamlit app:
  streamlit run ui/streamlit_app.py
```

### 7. Verify ChromaDB

Check that the database was created:

```bash
ls data/chroma_db/  # Should see ChromaDB files
```

---

## 🧪 Test the Ingestion

You can test individual ingestors in Python:

```python
from config.config import load_config
from src.ingestion.pdf_ingestor import ingest_pdf_directory
from src.rag.embedder import build_openai_embedder
from src.rag.vector_store import search_similar_chunks

# Test PDF ingestion
config = load_config()
chunks = ingest_pdf_directory("data/raw_pdfs", config.llama_cloud_api_key)
print(f"Found {len(chunks)} PDF chunks")

# Test vector search
embedder = build_openai_embedder(config.openai_api_key)
results = search_similar_chunks(
    query="What are the main operational risks?",
    embedder=embedder,
    persist_path=config.chroma_persist_path,
    collection_name=config.collection_name,
    top_k=3
)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['metadata']['source_file']}")
    print(f"   {result['content'][:200]}...")
```

---

## 📝 Next Steps

### Option A: Implement LangGraph Agent (3-4 hours)

**Files to create:**

1. **[src/agents/graph.py](src/agents/graph.py)** - Main agent workflow
2. **[src/tools/rag_tool.py](src/tools/rag_tool.py)** - Wrap retriever as tool
3. **[src/tools/analysis_tool.py](src/tools/analysis_tool.py)** - Structured analysis tool

See [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) for detailed implementation guide.

### Option B: Test Retrieval Directly

Create a test script:

```python
# test_retrieval.py
from config.config import load_config
from src.rag.retriever import retrieve_context, build_citations_from_chunks

config = load_config()

query = "What inventory items are running low?"
chunks = retrieve_context(
    query=query,
    openai_api_key=config.openai_api_key,
    persist_path=config.chroma_persist_path,
    collection_name=config.collection_name,
    top_k=5
)

citations = build_citations_from_chunks(chunks)

print(f"\nQuery: {query}")
print(f"Found {len(chunks)} relevant chunks:\n")

for i, citation in enumerate(citations, 1):
    print(f"{i}. [{citation.source_file}]")
    print(f"   {citation.relevant_excerpt}")
    print()
```

Run it:

```bash
python test_retrieval.py
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'llama_parse'"

**Fix:** Install dependencies again:

```bash
pip install --upgrade -r requirements.txt
```

### Issue: "LLAMA_CLOUD_API_KEY not found"

**Fix:** Make sure `.env` file exists and has valid keys:

```bash
cat .env  # Check file contents
```

Get API keys:
- LlamaCloud: https://cloud.llamaindex.ai/api-key
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

### Issue: "No PDF files found in data/raw_pdfs"

**Fix:** Add at least one PDF file to the directory:

```bash
ls data/raw_pdfs/  # Should show .pdf files
```

### Issue: ChromaDB errors

**Fix:** Delete and re-create the database:

```bash
rm -rf data/chroma_db/
python scripts/ingest_all.py
```

### Issue: Embedding errors (rate limits)

**Fix:** The code already handles this with batching. If you hit rate limits:

1. Reduce `EMBEDDING_BATCH_SIZE` in [src/rag/embedder.py](src/rag/embedder.py)
2. Add retry logic with exponential backoff

---

## 📚 Architecture Overview

```
User Query
    │
    ↓
[Streamlit UI] ← (Not yet implemented)
    │
    ↓
[LangGraph Agent] ← (Not yet implemented)
    │
    ├─→ [Retrieve Context] ← ✅ WORKS
    │       ↓
    │   [Vector Search] ← ✅ ChromaDB + OpenAI embeddings
    │
    ├─→ [Generate Answer] ← (Needs Claude integration)
    │
    └─→ [Format Output] ← (Needs implementation)
```

**What's working:**
- ✅ Data ingestion (PDF, CSV, CRM → chunks)
- ✅ Embeddings (OpenAI `text-embedding-3-small`)
- ✅ Vector search (ChromaDB with persistence)
- ✅ Citation building

**What's missing:**
- ⏳ LangGraph workflow orchestration
- ⏳ Claude API calls for answer generation
- ⏳ Streamlit chat interface

---

## 🎯 Success Criteria

You'll know it's working when:

1. ✅ `python scripts/ingest_all.py` completes without errors
2. ✅ `data/chroma_db/` folder has files (database created)
3. ✅ Test script retrieves relevant chunks for queries
4. ⏳ Streamlit app shows chat interface
5. ⏳ Queries return answers with source citations

---

## 📞 Need Help?

Check these files:
- [README.md](README.md) - Project overview
- [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) - Detailed status
- `.env.example` - Configuration template

---

*Ready to continue? Next: Implement LangGraph agent workflow!*
