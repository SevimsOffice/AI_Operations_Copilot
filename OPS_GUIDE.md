# Operations Guide - Atlas Operations Copilot

## Quick Diagnostics

### Check System Health
```bash
python ops_diagnostics.py
```

### Show Recent Errors
```bash
python ops_diagnostics.py --errors
```

### Find Incomplete Queries
```bash
python ops_diagnostics.py --incomplete
```

---

## Log Files

### 1. `execution-trace-default.jsonl` - Primary Diagnostic Tool
**What it tracks:**
- `query_start` - Query entered system
- `classification` - Query type and source assigned
- `retrieval_complete` - Chunks retrieved and sources
- `llm_generate_start` - Claude API call initiated
- `query_complete` - Final answer with citations

**Example healthy query:**
```json
{"stage": "query_start", "data": {"query": "how many complaints are open?"}}
{"stage": "classification", "data": {"query_type": "counting", "source_hint": "csv"}}
{"stage": "retrieval_complete", "data": {"chunk_count": 20, "source_types": {"csv": 20}}}
{"stage": "llm_generate_start", "data": {"model": "claude-sonnet-4"}}
{"stage": "query_complete", "data": {"answer_length": 450, "citation_count": 1}}
```

**Example failed query:**
```json
{"stage": "query_start", "data": {"query": "how many complaints are open?"}}
{"stage": "classification_error", "data": {"error_type": "ValueError", "error_message": "..."}}
```

---

### 2. `error-log.jsonl` - Error Details
**What it captures:**
- Error type (ValueError, TypeError, etc.)
- Error message
- Stage where it occurred
- Full context (query, scores, etc.)

**Example error:**
```json
{
  "timestamp": "2025-01-15T10:30:45",
  "session_id": "default",
  "stage": "classification",
  "error_type": "ValueError",
  "error_message": "COUNTING query did not classify to CSV. Got: crm.",
  "context": {
    "query": "how many customer complains are still open?",
    "csv_indicators": ["complaint", "complain", "record", ...],
    "crm_indicators": ["customer", "account", "client", ...]
  }
}
```

---

### 3. `streamlit_output.log` / `streamlit_debug.log`
Only captures Uvicorn startup. Use `execution-trace-default.jsonl` instead.

---

## Common Failure Patterns

### Pattern 1: Silent Classification Failure
**Symptom:**
```bash
grep "query_start" execution-trace-default.jsonl | tail -1
# Shows a query
grep "classification" execution-trace-default.jsonl | tail -1
# Nothing appears after that timestamp
```

**Diagnosis:**
```bash
python ops_diagnostics.py --incomplete
```

**What it means:** Query classifier threw an exception before logging

**Check:** `error-log.jsonl` for classification errors

---

### Pattern 2: Retrieval Returns Wrong Source
**Symptom:**
```json
{"stage": "classification", "data": {"query_type": "counting", "source_hint": "crm"}}
{"stage": "validation_error", "data": {"error": "COUNTING requires CSV, got crm"}}
```

**What it means:** Keyword scoring tied or favored wrong source

**Check:** Context in error log shows keyword matches

---

### Pattern 3: Query Started But Never Completed
**Symptom:**
```bash
python ops_diagnostics.py --incomplete
# Shows: 3 queries that never completed
```

**What it means:** Exception occurred after classification but before completion

**Check:**
1. `error-log.jsonl` for the query
2. Streamlit terminal output for Python traceback

---

## Diagnostic Commands

### Count errors by type
```bash
cat error-log.jsonl | python -c "
import sys, json
from collections import Counter
types = Counter(json.loads(l)['error_type'] for l in sys.stdin)
for error_type, count in types.most_common():
    print(f'{error_type}: {count}')
"
```

### Find queries that never completed
```bash
python -c "
import json
starts = set()
completes = set()
for line in open('execution-trace-default.jsonl'):
    e = json.loads(line)
    if e['stage'] == 'query_start':
        starts.add(e['data']['query'])
    elif e['stage'] == 'query_complete':
        completes.add(e['data'].get('query',''))
orphans = starts - completes
print(f'{len(orphans)} queries never completed')
for q in list(orphans)[:10]:
    print(f'  - {q[:80]}')
"
```

### Show last 10 queries
```bash
grep "query_start" execution-trace-default.jsonl | tail -10 | \
  python -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    print(f\"[{e['timestamp']}] {e['data']['query'][:70]}...\")
"
```

### Check if specific query completed
```bash
QUERY="how many complaints are open"
grep "$QUERY" execution-trace-default.jsonl
```

---

## What to Report in an Incident

1. **Error type** (from `error-log.jsonl`)
2. **Query that failed** (from context)
3. **Stage where it failed** (from trace log)
4. **Timestamp** (to correlate with other logs)
5. **Number of affected queries** (from `--incomplete`)

**Example incident report:**
```
Incident: Classification failures for counting queries
Time: 2025-01-15 10:30-10:45 UTC
Queries affected: 3
Error type: ValueError
Stage: classification
Root cause: Keyword "complains" not in CSV indicators
Fix: Added "complain" to csv_indicators list
Verification: All 3 queries now complete successfully
```

---

## Testing Error Logging

### Trigger a classification error (pre-fix):
```bash
# Run this query with the OLD code:
curl -X POST http://localhost:8501/query \
  -H "Content-Type: application/json" \
  -d '{"query": "how many customer complains are still open?"}'

# Check logs:
python ops_diagnostics.py --errors
```

### Expected output:
```
[ERROR LOG]
1. [2025-01-15T10:30:45] ValueError
   Stage: classification
   Message: COUNTING query did not classify to CSV. Got: crm.
   Query: how many customer complains are still open?...
```

---

## Monitoring in Production

### Set up a cron job to check for failures:
```bash
# crontab -e
*/5 * * * * cd /path/to/copilot && python ops_diagnostics.py --incomplete | mail -s "Copilot Failures" ops@company.com
```

### Log rotation:
```bash
# Rotate logs daily
0 0 * * * cd /path/to/copilot && mv execution-trace-default.jsonl execution-trace-$(date +\%Y\%m\%d).jsonl
```

### Alert on error rate:
```bash
# Alert if >10 errors in last hour
ERROR_COUNT=$(grep $(date -u +"%Y-%m-%dT%H" -d "1 hour ago") error-log.jsonl | wc -l)
if [ $ERROR_COUNT -gt 10 ]; then
  echo "High error rate: $ERROR_COUNT errors" | mail -s "ALERT: Copilot Errors" ops@company.com
fi
```

---

## Troubleshooting Checklist

- [ ] Run `python ops_diagnostics.py` for full health check
- [ ] Check `error-log.jsonl` for recent errors
- [ ] Find incomplete queries with `--incomplete`
- [ ] Check Streamlit terminal for Python tracebacks
- [ ] Verify ChromaDB is accessible
- [ ] Verify API keys are valid (OpenAI + Anthropic)
- [ ] Check disk space for vector store
- [ ] Clear Python cache: `find . -type d -name "__pycache__" -exec rm -rf {} +`
- [ ] Restart Streamlit: `streamlit run ui/streamlit_app.py`

---

## Contact

For issues with this system, check logs first, then escalate to the AI systems team with:
1. Output of `python ops_diagnostics.py`
2. Relevant lines from `error-log.jsonl`
3. The specific query that failed
