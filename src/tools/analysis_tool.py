"""Structured analysis tool for operational insight extraction."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from anthropic import Anthropic

from config.config import load_config
from src.models.schemas import AnalysisReport, OperationalInsight
from src.prompts.rag_prompt import get_analysis_system_prompt


def run_operational_analysis(query: str, retrieved_chunks: list[dict]) -> AnalysisReport:
    """Generate structured operational insights using Claude with structured output.

    Args:
        query: User's analysis query
        retrieved_chunks: Retrieved context chunks

    Returns:
        AnalysisReport with structured insights
    """
    if not retrieved_chunks:
        return AnalysisReport(
            query=query,
            insights=[],
            summary="No data available for analysis.",
            data_sources_used=[],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # Format context
    context_text = _format_chunks_for_analysis(retrieved_chunks)

    # Get unique data sources
    data_sources = list(set(
        chunk.get('metadata', {}).get('source_file', 'unknown')
        for chunk in retrieved_chunks
    ))

    config = load_config()

    try:
        client = Anthropic(api_key=config.anthropic_api_key)

        system_prompt = get_analysis_system_prompt()

        user_message = f"""Analyze the following operational data and identify key operational insights.

**Context Data:**
{context_text}

**Analysis Query:** {query}

Identify operational insights in these categories:
- **bottleneck**: Production constraints, capacity issues, process slowdowns
- **risk**: Quality issues, at-risk accounts, safety concerns, compliance gaps
- **opportunity**: Process improvements, cost savings, efficiency gains
- **action**: Required immediate actions, pending tasks, escalations

For each insight, provide:
1. Category (bottleneck, risk, opportunity, or action)
2. Title (short, descriptive)
3. Description (detailed explanation)
4. Severity (high, medium, or low)
5. Affected area (specific line, customer, system, or department)
6. Source references (which files mentioned this)
7. Recommended action (specific next steps)

Return insights as a JSON array following this structure:
```json
[
  {{
    "category": "risk",
    "title": "Recurring Hydraulic Seal Failures",
    "description": "SP-07 press has experienced 4 seal failures in 90 days, with 22.5 hours total downtime",
    "severity": "high",
    "affected_area": "Line 1 - Stamping Press SP-07",
    "source_references": ["maintenance_report_sample.txt"],
    "recommended_action": "Commission OEM inspection and evaluate full cylinder rebuild vs press replacement"
  }}
]
```

Analyze the data and return ONLY the JSON array of insights. No other text."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        response_text = message.content[0].text

        # Parse JSON response
        insights_data = _extract_json_from_response(response_text)

        # Convert to Pydantic models
        insights = []
        for item in insights_data:
            try:
                insight = OperationalInsight(**item)
                insights.append(insight)
            except Exception as e:
                print(f"Error parsing insight: {e}")
                continue

        # Generate summary
        summary = _generate_summary(insights, query)

        report = AnalysisReport(
            query=query,
            insights=insights,
            summary=summary,
            data_sources_used=data_sources,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        print(f"Error generating analysis: {e}")
        report = AnalysisReport(
            query=query,
            insights=[],
            summary=f"Error generating analysis: {str(e)}",
            data_sources_used=data_sources,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    return report


def _format_chunks_for_analysis(chunks: list[dict]) -> str:
    """Format chunks for analysis prompt."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get('metadata', {})
        source_file = metadata.get('source_file', 'unknown')
        content = chunk.get('content', '')

        context_parts.append(f"[{source_file}]: {content}")

    return "\n\n".join(context_parts)


def _extract_json_from_response(response_text: str) -> list[dict]:
    """Extract JSON array from Claude's response.

    Handles cases where Claude wraps JSON in markdown code blocks.
    """
    # Try to extract JSON from markdown code blocks
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()
    elif "```" in response_text:
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()
    else:
        json_text = response_text.strip()

    try:
        data = json.loads(json_text)
        if isinstance(data, list):
            return data
        else:
            return [data]
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response text: {response_text[:500]}")
        return []


def _generate_summary(insights: list[OperationalInsight], query: str) -> str:
    """Generate a summary of the insights."""
    if not insights:
        return "No significant operational insights identified from the available data."

    high_severity = [i for i in insights if i.severity == "high"]
    medium_severity = [i for i in insights if i.severity == "medium"]
    low_severity = [i for i in insights if i.severity == "low"]

    by_category = {}
    for insight in insights:
        by_category.setdefault(insight.category, []).append(insight)

    summary_parts = [
        f"Analysis identified {len(insights)} operational insights:"
    ]

    if high_severity:
        summary_parts.append(f"- {len(high_severity)} high-severity items requiring immediate attention")
    if medium_severity:
        summary_parts.append(f"- {len(medium_severity)} medium-severity items for review")
    if low_severity:
        summary_parts.append(f"- {len(low_severity)} low-severity optimization opportunities")

    summary_parts.append("\nBreakdown by category:")
    for category, items in by_category.items():
        summary_parts.append(f"- {category.capitalize()}: {len(items)}")

    return " ".join(summary_parts)
