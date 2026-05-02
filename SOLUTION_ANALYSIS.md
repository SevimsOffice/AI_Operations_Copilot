# Senior AI Systems Engineer's Approach to Classification Bug

## Problem Statement
```
Error: COUNTING query did not classify to CSV. Got: crm.
Query: 'how many customer complains are still open?'
```

## Investigation Process

### 1. Error Analysis (Don't Fix, Understand First)

**Question:** Why does COUNTING require CSV?
- CSV contains individual records (20 rows, 1 complaint per row)
- CRM contains aggregate summaries (customer-level data)
- Counting requires iterating individual records, not summaries
- This is an architectural constraint, not arbitrary

**Question:** What determines classification?
- Keyword-based scoring system
- CSV indicators: "complaint", "record", "transaction", etc.
- CRM indicators: "customer", "account", "client", etc.
- Highest score wins

**Question:** Why did it fail?
- Query contains "complains" (verb form)
- Classifier only checks for "complaint" (noun form)
- Query also contains "customer" (CRM indicator)
- Result: Tie or CRM wins → Error

### 2. Root Cause Analysis

**The Real Problem:** NLP tokenization issue
- "complains" ≠ "complaint" in substring matching
- System needs stemming or better word matching
- Current approach: exact substring match

**Scoring for failing query:**
```
"how many customer complains are still open?"
├─ CSV: "complaint" ❌ not found
├─ CRM: "customer" ✓ found (+1)
└─ Result: CRM wins → FAIL
```

**What we need:**
```
"how many customer complains are still open?"
├─ CSV: "complain" ✓ found in "complains" (+1)
├─ CRM: "customer" ✓ found (+1)
├─ Boost: "complain" found → CSV gets +0.5
└─ Result: CSV (1.5) > CRM (1) → SUCCESS
```

---

## Solution Design

### Option 1: Quick Fix (Substring Expansion) ⭐ RECOMMENDED
**Approach:** Add "complain" to catch all variations

**Pros:**
- Minimal code change
- Backwards compatible
- Handles: complaint, complains, complaining, complained
- No dependencies

**Cons:**
- Doesn't solve general NLP problem
- Still brittle for other word variations

**Implementation:**
```python
csv_indicators = [
    "complaint",
    "complain",  # catches all forms
    ...
]

# Update boost rule
if "complain" in query_lower and csv_score > 0:
    csv_score += 0.5
```

---

### Option 2: Stemming/Lemmatization (Proper NLP)
**Approach:** Use NLTK or spaCy for word normalization

**Pros:**
- Solves general problem (works for all word forms)
- More robust
- Production-grade

**Cons:**
- Adds dependency (nltk/spacy)
- Requires model download
- Slower processing
- Overkill for this specific issue

**Implementation:**
```python
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()

def normalize_query(query):
    words = query.lower().split()
    return [stemmer.stem(word) for word in words]

# Then match against stemmed indicators
```

---

### Option 3: Semantic Embeddings (Over-Engineering)
**Approach:** Use embeddings to find semantically similar words

**Pros:**
- Handles synonyms, not just word forms
- Very robust

**Cons:**
- Massive overkill
- Adds latency
- Requires embedding model
- Defeats purpose of fast keyword matching

---

### Option 4: Fine-tune LLM Classifier
**Approach:** Use an LLM to classify query intent

**Pros:**
- Most accurate
- Handles edge cases
- Natural language understanding

**Cons:**
- Adds API call latency
- Costs money per query
- Non-deterministic
- Defeats the purpose of having a fast classifier

---

## Recommended Solution: Option 1

**Why?**
1. **Solves the immediate problem** - "complains" now matches
2. **Minimal risk** - Only adds one keyword and modifies boost check
3. **No new dependencies** - Pure Python
4. **Fast** - No performance impact
5. **Testable** - Easy to verify

**When to revisit:**
- If we see 10+ similar issues with other word forms
- If we expand to multilingual queries
- If keyword list grows beyond 20-30 terms

---

## Implementation

### Code Changes

**File:** `src/rag/query_classifier.py`

```python
# Line 125: Add "complain" to CSV indicators
csv_indicators = [
    "complaint",
    "complain",  # matches "complains", "complaining", "complained"
    "record",
    "transaction",
    "item",
    "order",
    "status",
]

# Line 164: Update boost rule to check for "complain"
if "complain" in query_lower and csv_score > 0:
    csv_score += 0.5
```

---

## Testing Strategy

### 1. Unit Tests (Isolated)
```python
def test_complaint_variations():
    queries = [
        "how many customer complaints are open?",  # existing
        "how many customer complains are still open?",  # bug case
        "how many customers are complaining?",  # gerund
        "how many customers complained?",  # past tense
    ]
    for query in queries:
        assert infer_source_type(query) == "csv"
        assert classify_query(query) == QueryType.COUNTING
```

### 2. Integration Tests
```python
def test_end_to_end_counting():
    query = "how many customer complains are still open?"
    result = run_rag_query(query)
    assert "9" in result.answer
    assert result.confidence >= 0.8
```

### 3. Regression Tests
- Ensure existing queries still work
- Check that we didn't break CRM or PDF classification

---

## Deployment Considerations

### 1. Cache Invalidation ⚠️ CRITICAL
**Problem:** Python's `.pyc` bytecode cache can cause stale code

**Solution:**
```bash
# Clear cache before deployment
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Restart all services
systemctl restart streamlit  # or equivalent
```

**Why this matters:**
- Python compiles `.py` → `.pyc` for faster imports
- `.pyc` files are cached even if `.py` changes
- Streamlit long-running processes don't reload modules
- This is why the fix worked in CLI but not in Streamlit!

### 2. Monitoring
Add logging to track classification decisions:
```python
logger.info(
    f"Query classified: type={query_type}, source={source_hint}, "
    f"scores=(csv:{csv_score}, crm:{crm_score})"
)
```

### 3. Rollback Plan
- Git tag before deployment
- Keep old `.pyc` files as backup
- Monitor error rates for 24h post-deploy

---

## Prevention Strategies

### 1. Add More Test Cases
Include word variations in test suite:
```python
COMPLAINT_VARIATIONS = [
    "complaint", "complains", "complaining", "complained",
    "issue", "issues", "problem", "problems"
]
```

### 2. Consider Porter Stemmer for Future
If we see more morphological issues, upgrade to Option 2

### 3. Documentation
Document the architectural constraint:
```
COUNTING queries MUST classify to CSV because:
- CSV has individual records (countable)
- CRM has aggregates (not countable)
- Vector search with top-K would undercount
```

### 4. Better Error Messages
Current: `COUNTING query did not classify to CSV. Got: crm.`

Better:
```
COUNTING query classified to 'crm' but requires 'csv'.
Reason: Counting requires individual records, not aggregates.
Debug: CSV score=1.0, CRM score=1.0 (tie)
Hint: Check if query contains complaint-related keywords
```

---

## Lessons Learned

1. **Understand before fixing** - The error was informative, not just "broken"
2. **Test in isolation** - CLI test confirmed code was correct
3. **Check deployment env** - Cache invalidation is real
4. **Keep it simple** - Don't over-engineer (Option 1 > Option 3)
5. **Think prevention** - Add tests to catch regressions

---

## Timeline

1. **0-15 min:** Understand error, read code
2. **15-30 min:** Reproduce bug locally, trace execution
3. **30-45 min:** Design solution, evaluate options
4. **45-60 min:** Implement fix, write tests
5. **60-75 min:** Deploy, clear cache, verify
6. **75-90 min:** Document, add monitoring, write postmortem

---

## Success Criteria

✅ Query "how many customer complains are still open?" returns 9
✅ Existing queries still work (regression test passes)
✅ Performance unchanged (<1ms classification)
✅ No new dependencies added
✅ Documented for future engineers
