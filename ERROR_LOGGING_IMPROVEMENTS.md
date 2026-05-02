# Error Logging Improvements - For Production Ops

## Problem Statement

**Before:** Queries failed silently with no trace of what went wrong.

```json
// What ops saw in logs:
{"stage": "query_start", "data": {"query": "how many customer complains..."}}
// ... silence ... nothing more
```

**Impact:**
- No visibility into failures
- Can't diagnose root cause
- Can't measure error rates
- Can't detect patterns

---

## Solution Implemented (15 minutes)

### 1. Added Error Logging to Tracer (`src/execution/tracer.py`)

**New method: `log_error(stage, error, context)`**

```python
def log_error(self, stage: str, error: Exception, context: dict):
    """Log an error with full context for ops debugging."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": self.session_id,
        "stage": stage,
        "error_type": type(error).__name__,     # ValueError, TypeError, etc.
        "error_message": str(error),            # Full error message
        "context": context                      # Query, scores, indicators, etc.
    }
    # Writes to error-log.jsonl (separate from trace log)
    # Also writes to trace log as {stage}_error for timeline continuity
```

---

### 2. Wrapped Query Classifier (`src/rag/smart_retriever.py`)

**Now catches and logs classification errors:**

```python
try:
    query_type = classify_query(query)
    source_hint = infer_source_type(query)
    tracer.log("classification", {...})
except Exception as e:
    tracer.log_error("classification", e, {
        "query": query,
        "csv_indicators": [...],
        "crm_indicators": [...]
    })
    raise  # Re-raise so caller knows it failed
```

---

### 3. Error Handling in Graph Nodes (`src/agents/graph.py`)

**Retrieve context node now logs errors:**

```python
except Exception as e:
    tracer.log_error("retrieve_context", e, {
        "query": state.get("query"),
        "state_keys": list(state.keys())
    })
    state["error"] = f"Retrieval failed: {str(e)}"
    # Continues gracefully instead of crashing
```

---

### 4. Ops Diagnostic Tool (`ops_diagnostics.py`)

**Single command to check system health:**

```bash
python ops_diagnostics.py              # Full health check
python ops_diagnostics.py --errors     # Show error details
python ops_diagnostics.py --incomplete # Find incomplete queries
```

**Output example:**
```
[1] TRACE LOG STATUS
  ✓ 45 entries logged
  Stages: {'query_start': 10, 'classification': 8, 'retrieval_complete': 8, ...}

[2] ERROR LOG STATUS
  ⚠ 2 errors logged

  Total errors: 2
  By type:
    ValueError: 2
  By stage:
    classification: 2

[3] INCOMPLETE QUERIES
  ⚠ 2 incomplete queries
    [2026-05-02T09:30:45] how many customer complains are still open?...
    [2026-05-02T09:32:12] how many customers complained last month?...
```

---

## What Ops Gets Now

### Before Fix
```json
// execution-trace-default.jsonl
{"stage": "query_start", "data": {"query": "..."}}
// nothing - silent failure
```

### After Fix
```json
// execution-trace-default.jsonl
{"stage": "query_start", "data": {"query": "how many customer complains..."}}
{"stage": "classification_error", "data": {
  "error_type": "ValueError",
  "error_message": "COUNTING query did not classify to CSV. Got: crm.",
  "query": "how many customer complains...",
  "csv_indicators": ["complaint", "complain", ...],
  "crm_indicators": ["customer", "account", ...]
}}

// error-log.jsonl (dedicated error log)
{
  "timestamp": "2026-05-02T10:05:20",
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

## Ops Diagnostic Commands

### Find incomplete queries (queries that started but never finished)
```bash
python ops_diagnostics.py --incomplete
```

### Show recent errors with context
```bash
python ops_diagnostics.py --errors
```

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

### Find all queries that never completed
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
print(f'{len(orphans)} queries never completed:')
for q in orphans:
    print(f'  - {q}')
"
```

---

## Demo Script

### Show the problem (before fix)
1. Show old trace log with silent failures
2. Point out: query_start → nothing
3. Explain: "No way to diagnose what went wrong"

### Show the solution (after fix)
1. Run: `python test_error_logging.py`
2. Show: Error appears in both error-log.jsonl and trace log
3. Run: `python ops_diagnostics.py --errors`
4. Show: Full context captured (query, scores, indicators)

### Show ops workflow
1. Run: `python ops_diagnostics.py`
2. Show: Health check output
3. Show: Incomplete queries detected
4. Show: Error summary by type

**Time: 2 minutes in video**

---

## Files Changed

1. **src/execution/tracer.py** - Added `log_error()` method
2. **src/rag/smart_retriever.py** - Wrapped classifier with try/catch
3. **src/agents/graph.py** - Added error handling to retrieve_context
4. **ops_diagnostics.py** - New ops diagnostic tool (NEW FILE)
5. **OPS_GUIDE.md** - Operations guide for production (NEW FILE)

---

## Testing

```bash
# Test error logging works
python test_error_logging.py

# Should show:
# [OK] Error log created
# [OK] Contains 1 error(s)
# [OK] Found error in trace log
# [OK] ops_diagnostics.py shows error details
```

---

## Production Monitoring

### Set up cron job to alert on failures
```bash
# Check every 5 minutes
*/5 * * * * cd /path/to/copilot && python ops_diagnostics.py --incomplete | mail -s "Copilot Failures" ops@company.com
```

### Log rotation
```bash
# Daily rotation
0 0 * * * cd /path/to/copilot && mv execution-trace-default.jsonl execution-trace-$(date +\%Y\%m\%d).jsonl
```

### Alert on high error rate
```bash
ERROR_COUNT=$(grep $(date -u +"%Y-%m-%dT%H" -d "1 hour ago") error-log.jsonl | wc -l)
if [ $ERROR_COUNT -gt 10 ]; then
  echo "High error rate: $ERROR_COUNT errors" | mail -s "ALERT" ops@company.com
fi
```

---

## Impact

| Metric | Before | After |
|--------|--------|-------|
| Silent failures | Yes | No |
| Error visibility | None | Full context |
| Diagnostic time | Unknown | <1 minute |
| Error tracking | Manual | Automated |
| Incomplete query detection | Not possible | Automated |

---

## Next Steps (If You Had More Time)

1. **Structured error codes** - Map error types to error codes (ERR-001, ERR-002)
2. **Prometheus metrics** - Export error counts as metrics
3. **Grafana dashboard** - Visualize error rates over time
4. **Alerting rules** - Auto-alert on error spikes
5. **Error replay** - Tool to re-run failed queries after fix

**But for 30 minutes, this is production-ready ops tooling.**
