"""Application entry point for Atlas Operations Copilot.

This module exposes a simple entry function so the project can be started
from a single place during local development or future deployment wiring.
"""

from __future__ import annotations

from ui.streamlit_app import run_streamlit_app


def main() -> None:
    """Run the default application entrypoint."""
    # Architecture note: the Streamlit app is the primary interface surface.
    run_streamlit_app()


if __name__ == "__main__":
    main()
