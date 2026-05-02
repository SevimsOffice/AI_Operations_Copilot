# Atlas Operations Copilot

Atlas Operations Copilot is a production-oriented AI assistant skeleton that ingests operational data from PDFs, CSV files, and mock CRM JSON records, stores semantic vectors in a local ChromaDB index, and answers operator questions through a LangGraph workflow with source citations and optional structured insight analysis in a Streamlit chat UI.

## Architecture Diagram

```text
+-------------------+     +-------------------+     +-------------------+
|   PDF documents   |     |     CSV files     |     |    CRM JSON       |
| data/raw_pdfs/    |     | data/raw_csv/     |     | data/mock_crm/    |
+---------+---------+     +---------+---------+     +---------+---------+
          \                     |                           /
           \                    |                          /
            +-------------------+-------------------------+
                                |
                       +--------v--------+
                       |  Ingestion      |
                       |  (chunking)     |
                       +--------+--------+
                                |
                       +--------v--------+
                       |  Embeddings     |
                       | OpenAI small    |
                       +--------+--------+
                                |
                       +--------v--------+
                       | ChromaDB Local  |
                       | data/chroma_db  |
                       +--------+--------+
                                |
                       +--------v--------+
                       |   LangGraph     |
                       | retrieve/answer |
                       | analyze/format  |
                       +--------+--------+
                                |
                       +--------v--------+
                       |   Streamlit UI  |
                       |  chat frontend  |
                       +-----------------+
```

## Setup Instructions

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy environment template and set secrets:
   - `copy .env.example .env` (Windows) or `cp .env.example .env` (macOS/Linux)
4. Fill `.env` values for:
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`
   - `LLAMA_CLOUD_API_KEY`
5. Place source data into:
   - `data/raw_pdfs/`
   - `data/raw_csv/`
   - `data/mock_crm/`

## How To Ingest Data

Run the ingestion orchestrator once to parse, chunk, embed, and index all available sources:

`python scripts/ingest_all.py`

## How To Run

Start the Streamlit UI:

`streamlit run ui/streamlit_app.py`

## Key Architecture Decisions

- LangGraph is used to model a stateful workflow with conditional branching, making it easy to route simple Q&A requests differently from deeper operational analysis.
- ChromaDB is used as a local persistent vector store so the project runs without an additional managed database service.
- OpenAI embeddings are paired with Claude generation to combine robust semantic retrieval quality with strong synthesis and reasoning.
- LlamaParse is chosen for PDF ingestion because it handles complex formatting and tables better than plain text extraction pipelines.
- A separate analysis node/tool is included so structured operational insights can be produced in schema-validated form, rather than mixed into unstructured answer text.

## Data Sources Description

- PDF sources: policy docs, SOPs, reports, and operational playbooks in `data/raw_pdfs/`.
- CSV sources: metrics exports, inventories, and tabular operational snapshots in `data/raw_csv/`.
- CRM sources: account, pipeline, and customer operation snapshots as JSON in `data/mock_crm/`.
