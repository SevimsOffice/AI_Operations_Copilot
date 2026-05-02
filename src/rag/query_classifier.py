"""Query classification for intelligent retrieval routing."""

from __future__ import annotations

from enum import Enum


class QueryType(Enum):
    """Types of queries that require different retrieval strategies."""

    COUNTING = "counting"  # "how many", "count", "total number"
    SEMANTIC = "semantic"  # General semantic questions
    LISTING = "listing"    # "list all", "show me all"


def classify_query(query: str) -> QueryType:
    """Classify query to determine optimal retrieval strategy.

    Args:
        query: User's query string

    Returns:
        QueryType enum indicating the query classification

    Examples:
        "How many complaints are open?" -> COUNTING
        "What are the main issues?" -> SEMANTIC
        "List all customers with complaints" -> LISTING
    """
    query_lower = query.lower()

    # Counting indicators
    counting_keywords = [
        "how many",
        "count",
        "total number",
        "number of",
        "how much",
        "quantity",
        "sum of",
        "total",
    ]

    # Listing indicators
    listing_keywords = [
        "list all",
        "show all",
        "show me all",
        "give me all",
        "list every",
        "all the",
    ]

    # Check for counting queries
    for keyword in counting_keywords:
        if keyword in query_lower:
            query_type = QueryType.COUNTING

            # VALIDATION: Counting queries MUST classify to CSV
            source_hint = infer_source_type(query)
            if source_hint != "csv":
                raise ValueError(
                    f"COUNTING query did not classify to CSV. "
                    f"Got: {source_hint}. Query: '{query}'"
                )

            return query_type

    # Check for listing queries
    for keyword in listing_keywords:
        if keyword in query_lower:
            return QueryType.LISTING

    # Default to semantic search
    return QueryType.SEMANTIC


def extract_count_target(query: str) -> str | None:
    """Extract what entity to count from a counting query.

    Args:
        query: User's query string

    Returns:
        Target entity type (e.g., "complaints", "customers") or None

    Examples:
        "How many complaints are open?" -> "complaints"
        "How many customers have issues?" -> "customers"
    """
    query_lower = query.lower()

    # Common entities to count
    entities = {
        "complaint": ["complaint", "complain", "issue", "problem"],
        "customer": ["customer", "client", "account"],
        "incident": ["incident", "event", "occurrence"],
        "item": ["item", "product", "part"],
    }

    for entity_type, keywords in entities.items():
        for keyword in keywords:
            if keyword in query_lower:
                return entity_type

    return None


def infer_source_type(query: str) -> str | None:
    """Infer which source type is most relevant for the query.

    Args:
        query: User's query string

    Returns:
        Source type hint ("csv", "crm", "pdf") or None

    This helps optimize retrieval by focusing on the right data source.
    """
    query_lower = query.lower()

    # CSV typically contains: complaints, records, transactions, items
    csv_indicators = [
        "complaint",
        "complain",  # matches "complains", "complaining", "complained"
        "record",
        "transaction",
        "item",
        "order",
        "status",
    ]

    # CRM typically contains: customers, accounts, relationships
    crm_indicators = [
        "customer",
        "account",
        "client",
        "company",
        "contact",
    ]

    # PDF typically contains: reports, procedures, documentation
    pdf_indicators = [
        "report",
        "procedure",
        "policy",
        "document",
        "guideline",
        "maintenance",
        "operational",
    ]

    # Score each source type
    csv_score = sum(1 for indicator in csv_indicators if indicator in query_lower)
    crm_score = sum(1 for indicator in crm_indicators if indicator in query_lower)
    pdf_score = sum(1 for indicator in pdf_indicators if indicator in query_lower)

    # Return source with highest score
    if max(csv_score, crm_score, pdf_score) == 0:
        return None

    # Special case: "complain" is a strong indicator for CSV even if "customer" is present
    # This handles queries like "How many customer complaints are open?"
    if "complain" in query_lower and csv_score > 0:
        # Boost CSV score to break tie
        csv_score += 0.5

    # Use strict comparison to prevent ties
    if csv_score > crm_score and csv_score > pdf_score:
        return "csv"
    elif crm_score > pdf_score and crm_score > csv_score:
        return "crm"
    elif pdf_score > csv_score and pdf_score > crm_score:
        return "pdf"
    else:
        # Tie detected - cannot classify deterministically
        return None
