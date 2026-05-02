"""Test that the system correctly counts complaints from CSV data."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.agents.graph import build_copilot_graph

print("=" * 70)
print("TESTING COUNTING ACCURACY")
print("=" * 70)

# The correct answer from your CSV data
EXPECTED_OPEN_COMPLAINTS = 9

test_query = "How many customer complaints are still open?"

print(f"\n[QUERY] {test_query}")
print(f"\n[EXPECTED ANSWER] 9 open complaints")
print("\nRunning query through agent...\n")

try:
    graph = build_copilot_graph()

    result = graph.invoke({
        "query": test_query,
        "retrieved_chunks": [],
        "rag_response": None,
        "analysis_report": None,
        "error": None,
    })

    if result.get("rag_response"):
        answer = result["rag_response"].answer

        print("=" * 70)
        print("ANSWER")
        print("=" * 70)
        print(f"\n{answer}\n")

        # Check if answer mentions correct number
        if "9" in answer and ("9 open" in answer.lower() or "nine" in answer.lower()):
            print("\n[SUCCESS] ✓ Answer mentions 9 open complaints - CORRECT!")
        elif "10" in answer or "ten" in answer.lower():
            print("\n[WARNING] ✗ Answer still mentions 10 - needs more refinement")
        else:
            print("\n[INFO] Check answer manually to verify correctness")

        print(f"\nConfidence: {int(result['rag_response'].confidence * 100)}%")
        print(f"Citations: {len(result['rag_response'].citations)} sources")

except Exception as e:
    print(f"\n[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
