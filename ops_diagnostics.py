#!/usr/bin/env python3
"""Ops diagnostic tool for Atlas Operations Copilot.

Usage:
    python ops_diagnostics.py               # Full health check
    python ops_diagnostics.py --errors      # Show only errors
    python ops_diagnostics.py --incomplete  # Show incomplete queries
"""

import json
import sys
from collections import Counter
from pathlib import Path

# File paths
TRACE_LOG = Path("execution-trace-default.jsonl")
ERROR_LOG = Path("error-log.jsonl")


def load_jsonl(path):
    """Load JSONL file, return empty list if not found."""
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f]


def check_incomplete_queries():
    """Find queries that started but never completed."""
    entries = load_jsonl(TRACE_LOG)

    starts = {}  # query -> timestamp
    completes = set()

    for entry in entries:
        stage = entry.get("stage")
        if stage == "query_start":
            query = entry["data"]["query"]
            starts[query] = entry["timestamp"]
        elif stage == "query_complete":
            query = entry["data"].get("query", "")
            completes.add(query)

    incomplete = {q: ts for q, ts in starts.items() if q not in completes}
    return incomplete


def check_errors():
    """Show all logged errors."""
    errors = load_jsonl(ERROR_LOG)
    return errors


def check_classification_errors():
    """Show classification-specific errors with context."""
    errors = [e for e in load_jsonl(ERROR_LOG) if "classification" in e.get("stage", "")]
    return errors


def show_recent_activity(limit=10):
    """Show last N queries."""
    entries = load_jsonl(TRACE_LOG)
    query_starts = [e for e in entries if e.get("stage") == "query_start"]
    return query_starts[-limit:]


def show_error_summary():
    """Show error counts by type."""
    errors = load_jsonl(ERROR_LOG)
    if not errors:
        return "No errors logged"

    error_types = Counter(e.get("error_type") for e in errors)
    error_stages = Counter(e.get("stage") for e in errors)

    summary = []
    summary.append(f"Total errors: {len(errors)}")
    summary.append("\nBy type:")
    for error_type, count in error_types.most_common():
        summary.append(f"  {error_type}: {count}")
    summary.append("\nBy stage:")
    for stage, count in error_stages.most_common():
        summary.append(f"  {stage}: {count}")

    return "\n".join(summary)


def main():
    print("="*70)
    print("ATLAS OPERATIONS COPILOT - OPS DIAGNOSTICS")
    print("="*70)

    if "--errors" in sys.argv:
        print("\n[ERROR LOG]")
        errors = check_errors()
        if not errors:
            print("No errors logged [OK]")
        else:
            for i, error in enumerate(errors[-10:], 1):
                print(f"\n{i}. [{error['timestamp']}] {error['error_type']}")
                print(f"   Stage: {error['stage']}")
                print(f"   Message: {error['error_message']}")
                if error.get('context', {}).get('query'):
                    print(f"   Query: {error['context']['query'][:80]}...")
        return

    if "--incomplete" in sys.argv:
        print("\n[INCOMPLETE QUERIES]")
        incomplete = check_incomplete_queries()
        if not incomplete:
            print("No incomplete queries [OK]")
        else:
            print(f"Found {len(incomplete)} queries that never completed:")
            for query, ts in list(incomplete.items())[:10]:
                print(f"  [{ts}] {query[:80]}...")
        return

    # Full health check
    print("\n[1] TRACE LOG STATUS")
    if TRACE_LOG.exists():
        entries = load_jsonl(TRACE_LOG)
        print(f"  [OK] {len(entries)} entries logged")
        stages = Counter(e.get("stage") for e in entries)
        print(f"  Stages: {dict(stages)}")
    else:
        print("  [X] No trace log found")

    print("\n[2] ERROR LOG STATUS")
    if ERROR_LOG.exists():
        errors = load_jsonl(ERROR_LOG)
        if errors:
            print(f"  [!] {len(errors)} errors logged")
            print(f"\n{show_error_summary()}")
        else:
            print("  [OK] No errors logged")
    else:
        print("  [OK] No error log (no errors occurred)")

    print("\n[3] INCOMPLETE QUERIES")
    incomplete = check_incomplete_queries()
    if incomplete:
        print(f"  [!] {len(incomplete)} incomplete queries")
        for query, ts in list(incomplete.items())[:5]:
            print(f"    [{ts}] {query[:60]}...")
    else:
        print("  [OK] All queries completed")

    print("\n[4] RECENT ACTIVITY (last 5 queries)")
    recent = show_recent_activity(5)
    if recent:
        for entry in recent:
            query = entry["data"]["query"]
            ts = entry["timestamp"]
            print(f"  [{ts}] {query[:60]}...")
    else:
        print("  No queries logged yet")

    print("\n[5] CLASSIFICATION ERRORS")
    classification_errors = check_classification_errors()
    if classification_errors:
        print(f"  [!] {len(classification_errors)} classification errors")
        for error in classification_errors[-3:]:
            print(f"\n  [{error['timestamp']}] {error['error_type']}")
            print(f"    Message: {error['error_message']}")
            if error.get('context', {}).get('query'):
                print(f"    Query: {error['context']['query'][:70]}...")
    else:
        print("  [OK] No classification errors")

    print("\n" + "="*70)
    print("DIAGNOSTIC OPTIONS:")
    print("  python ops_diagnostics.py --errors      # Show error details")
    print("  python ops_diagnostics.py --incomplete  # Show incomplete queries")
    print("="*70)


if __name__ == "__main__":
    main()
