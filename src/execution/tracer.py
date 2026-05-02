"""Execution tracing for debugging."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ExecutionTracer:
    """Logs execution boundaries for debugging."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.log_file = Path(__file__).parents[2] / f"execution-trace-{session_id}.jsonl"
        self.error_log = Path(__file__).parents[2] / "error-log.jsonl"

    def log(self, stage: str, data: dict[str, Any]) -> None:
        """Log a stage of execution."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "stage": stage,
            "data": data
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")

    def log_error(self, stage: str, error: Exception, context: dict[str, Any]) -> None:
        """Log an error with full context for ops debugging."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        # Write to error log
        with open(self.error_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
        # Also write to main trace log for timeline continuity
        self.log(f"{stage}_error", {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **context
        })


# Global tracer instance
tracer = ExecutionTracer()
