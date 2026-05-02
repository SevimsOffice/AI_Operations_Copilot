"""Streamlit chat interface for Atlas Operations Copilot."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from src.agents.graph import build_copilot_graph


def run_streamlit_app() -> None:
    """Render and run the Streamlit chat interface."""
    st.set_page_config(
        page_title="Atlas Operations Copilot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🤖 Atlas Operations Copilot")
    st.markdown("*Ask operational questions grounded in your manufacturing data*")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "citations" not in st.session_state:
        st.session_state.citations = []
    if "analysis_report" not in st.session_state:
        st.session_state.analysis_report = None

    # Sidebar - Data Sources & Citations
    with st.sidebar:
        st.header("📚 Information")

        with st.expander("ℹ️ About", expanded=False):
            st.markdown("""
**Atlas Operations Copilot** analyzes your operational data from:
- 📄 PDF documents (maintenance reports, procedures)
- 📊 CSV files (complaints, metrics, inventories)
- 🗂️ CRM data (customer accounts, issues)

**Features:**
- Retrieval-Augmented Generation (RAG)
- Source citation tracking
- Structured operational analysis
- Powered by Claude Sonnet 4
            """)

        st.divider()

        st.subheader("📎 Sources")
        if st.session_state.citations:
            for i, citation in enumerate(st.session_state.citations, 1):
                with st.container():
                    st.markdown(f"**{i}. {citation.source_file}**")
                    st.caption(f"Type: {citation.source_type}")
                    with st.expander("View excerpt"):
                        st.text(citation.relevant_excerpt)
        else:
            st.info("Citations will appear here after you ask a question")

        # Analysis Report (if triggered)
        if st.session_state.analysis_report:
            st.divider()
            st.subheader("📊 Analysis Report")

            report = st.session_state.analysis_report

            # Summary
            st.markdown("**Summary:**")
            st.info(report.summary)

            # Insights
            if report.insights:
                st.markdown(f"**Insights ({len(report.insights)}):**")

                for insight in report.insights:
                    # Color-code by severity
                    if insight.severity == "high":
                        st.error(f"🔴 **{insight.title}**")
                    elif insight.severity == "medium":
                        st.warning(f"🟡 **{insight.title}**")
                    else:
                        st.success(f"🟢 **{insight.title}**")

                    with st.expander(f"Details - {insight.category}"):
                        st.markdown(f"**Category:** {insight.category}")
                        st.markdown(f"**Severity:** {insight.severity}")
                        st.markdown(f"**Affected Area:** {insight.affected_area}")
                        st.markdown(f"**Description:**\n{insight.description}")
                        st.markdown(f"**Recommended Action:**\n{insight.recommended_action}")
                        if insight.source_references:
                            st.markdown(f"**Sources:** {', '.join(insight.source_references)}")

    # Main chat interface
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_query = st.chat_input("Ask about operations, risks, bottlenecks, or insights...")

    if user_query:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_query})

        with st.chat_message("user"):
            st.markdown(user_query)

        # Show thinking indicator
        with st.chat_message("assistant"):
            with st.spinner("Analyzing operational data..."):
                try:
                    # Build and invoke graph
                    graph = build_copilot_graph()

                    initial_state = {
                        "query": user_query,
                        "retrieved_chunks": [],
                        "rag_response": None,
                        "analysis_report": None,
                        "error": None,
                    }

                    print(f"\n[UI DEBUG] Invoking graph for query: {user_query[:50]}")
                    result = graph.invoke(initial_state)
                    print(f"[UI DEBUG] Graph returned: {result.keys() if result else 'None'}")

                    # Debug: check what graph returned
                    if not result:
                        st.error("Graph returned None")
                        result = {"error": "Graph invocation returned None"}

                    print(f"[DEBUG] Graph result keys: {result.keys() if result else 'None'}")
                    print(f"[DEBUG] rag_response type: {type(result.get('rag_response')) if result else 'N/A'}")

                    # Extract response with null safety
                    rag_response = result.get("rag_response") if result else None
                    analysis_report = result.get("analysis_report") if result else None
                    error = result.get("error") if result else None

                    if error:
                        st.error(f"Error: {error}")
                        answer = f"Sorry, an error occurred: {error}"

                    elif rag_response:
                        # DEBUG: Show what was retrieved
                        retrieved_chunks = result.get("retrieved_chunks", []) if result else []
                        if retrieved_chunks:
                            source_types = []
                            for c in retrieved_chunks:
                                if c and isinstance(c, dict):
                                    src_type = c.get('metadata', {}).get('source_type', 'unknown') if c.get('metadata') else 'unknown'
                                    source_types.append(src_type)
                            from collections import Counter
                            type_counts = Counter(source_types)
                            st.info(f"DEBUG: Retrieved {len(retrieved_chunks)} chunks: {dict(type_counts)}")

                        answer = rag_response.answer if rag_response.answer else "No answer generated"

                        # Update citations in sidebar (handle None case)
                        if rag_response.citations:
                            st.session_state.citations = rag_response.citations

                        # Update analysis report if available
                        if analysis_report:
                            st.session_state.analysis_report = analysis_report

                        # Display answer
                        st.markdown(answer)

                        # Show confidence
                        if rag_response.confidence > 0:
                            confidence_pct = int(rag_response.confidence * 100)
                            st.caption(f"Confidence: {confidence_pct}%")

                        # Show number of citations
                        if rag_response.citations:
                            st.caption(f"📎 {len(rag_response.citations)} sources cited (see sidebar)")

                    else:
                        answer = "No response generated. Please try again."
                        st.warning(answer)

                    # Add assistant response to history
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    error_msg = f"Error processing query: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🤖 Powered by Claude Sonnet 4")
    with col2:
        st.caption("📊 OpenAI Embeddings + ChromaDB")
    with col3:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.citations = []
            st.session_state.analysis_report = None
            st.rerun()


if __name__ == "__main__":
    run_streamlit_app()
