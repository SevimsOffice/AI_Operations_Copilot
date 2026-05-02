# Known Limitation: Counting Queries

## Issue:
When asking "how many complaints are open?", the system may return incomplete counts.

## Root Cause:
- Vector search retrieves top-K most similar chunks (default: 10)
- CSV file has 20 rows (20 chunks), but query only retrieves ~2-3 CSV chunks
- LLM can only count what it sees in retrieved context
- Result: Undercounting

## Current Answer:
- System says: **2 open complaints** (only counts what it retrieved)
- Actual answer from CSV: **9 open complaints**

## Why This Happens:
Query "how many complaints open?" semantically matches:
- ✅ CRM summaries (have "open_complaints" field)  
- ❌ Individual CSV rows less strongly

So vector search prioritizes CRM chunks over CSV chunks.

## Solutions:

### Solution 1: Increase Retrieval (Already Implemented)
Changed `top_k` from 5 to 10 - helps but not enough for 20 rows

### Solution 2: Retrieve ALL CSV chunks for counting
For counting queries, retrieve ALL chunks of relevant type:
```python
if "how many" in query.lower():
    # Get ALL CSV chunks instead of top-K
    chunks = get_all_chunks_by_type('csv')
```

### Solution 3: Pre-aggregated Answers
Add metadata with pre-counted values:
- "total_complaints": 20
- "open_complaints": 9
- "resolved_complaints": 11

### Solution 4: Hybrid Search
Use metadata filtering + semantic search:
```python
# First: Get all CSV chunks
# Then: Semantic search within those
```

## For Demo:
**Explain this as an architectural trade-off:**

> "The system uses vector similarity search which is great for semantic questions like 'what are the main issues?' but has a known limitation for aggregate counting queries. In production, we'd implement hybrid search or metadata filtering for 'how many' questions. This is a classic RAG trade-off between semantic search power and exhaustive retrieval."

This shows understanding of the limitation and ability to articulate solutions.
