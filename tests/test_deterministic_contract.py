"""Deterministic execution contract tests."""

import pytest
from src.tools.rag_tool import run_rag_query
from src.rag.query_classifier import QueryType, classify_query
from config.config import load_config


# Fixed test cases with expected outputs
TEST_CASES = [
    {
        "name": "counting_open_complaints",
        "query": "How many customer complaints are open?",
        "expected_classification": QueryType.COUNTING,
        "expected_source_type": "csv",
        "expected_chunk_count": 20,  # All CSV chunks
        "expected_answer_contains": "9",  # Correct count
        "expected_confidence_min": 0.8,
    },
    {
        "name": "q3_2025_bottlenecks",
        "query": "What were the top operational bottlenecks in Q3 2025?",
        "expected_classification": QueryType.SEMANTIC,
        "expected_source_type": "pdf",
        "expected_chunk_count_min": 5,
        "expected_answer_contains": "coolant",
        "expected_confidence_min": 0.7,
    },
    {
        "name": "customer_summary",
        "query": "Which customers are at risk?",
        "expected_classification": QueryType.SEMANTIC,
        "expected_source_type": "crm",
        "expected_chunk_count_min": 3,
        "expected_answer_contains": "relationship_health",
        "expected_confidence_min": 0.6,
    },
]


@pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda tc: tc["name"])
def test_deterministic_execution(test_case):
    """Verify deterministic execution contract."""
    config = load_config()
    query = test_case["query"]

    # Step 1: Verify classification
    query_type = classify_query(query)
    assert query_type == test_case["expected_classification"], (
        f"Classification mismatch: got {query_type.value}, "
        f"expected {test_case['expected_classification'].value}"
    )

    # Step 2: Execute query
    chunks, rag_response = run_rag_query(
        query=query,
        openai_api_key=config.openai_api_key,
        persist_path=config.chroma_persist_path,
        collection_name=config.collection_name,
    )

    # Step 3: Verify chunk retrieval
    assert len(chunks) > 0, "Retrieved 0 chunks"

    if "expected_chunk_count" in test_case:
        assert len(chunks) == test_case["expected_chunk_count"], (
            f"Chunk count mismatch: got {len(chunks)}, "
            f"expected {test_case['expected_chunk_count']}"
        )

    if "expected_chunk_count_min" in test_case:
        assert len(chunks) >= test_case["expected_chunk_count_min"], (
            f"Too few chunks: got {len(chunks)}, "
            f"expected >= {test_case['expected_chunk_count_min']}"
        )

    # Step 4: Verify source type
    source_types = {c.get('metadata', {}).get('source_type') for c in chunks}
    assert test_case["expected_source_type"] in source_types, (
        f"Source type mismatch: got {source_types}, "
        f"expected {test_case['expected_source_type']}"
    )

    # Step 5: Verify RAG response
    assert rag_response is not None, "RAG response is None"
    assert rag_response.answer, "Answer is empty"
    assert test_case["expected_answer_contains"].lower() in rag_response.answer.lower(), (
        f"Answer does not contain '{test_case['expected_answer_contains']}'"
    )
    assert rag_response.confidence >= test_case["expected_confidence_min"], (
        f"Confidence too low: {rag_response.confidence}"
    )


def test_counting_returns_exact_nine():
    """Specific test for the known bug: must return 9, not 10."""
    config = load_config()

    chunks, rag_response = run_rag_query(
        query="How many customer complaints are open?",
        openai_api_key=config.openai_api_key,
        persist_path=config.chroma_persist_path,
        collection_name=config.collection_name,
    )

    # Must retrieve all 20 CSV chunks
    assert len(chunks) == 20, f"Expected 20 chunks, got {len(chunks)}"

    # All must be CSV
    source_types = {c.get('metadata', {}).get('source_type') for c in chunks}
    assert source_types == {'csv'}, f"Expected only CSV, got {source_types}"

    # Answer must contain "9" but NOT "10"
    answer_lower = rag_response.answer.lower()
    assert "9" in answer_lower or "nine" in answer_lower, (
        f"Answer does not contain '9': {rag_response.answer[:200]}"
    )

    # Verify it's not miscounting to 10
    if "10" in answer_lower or "ten" in answer_lower:
        # Check if it's saying "10 resolved" or similar (acceptable)
        # but not "10 open" (bug)
        assert "10 open" not in answer_lower and "ten open" not in answer_lower, (
            "Answer incorrectly states 10 open complaints"
        )
