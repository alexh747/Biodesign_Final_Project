"""
recommendation.py
=================
Shared data type for the optimization & error-checking module.

A Recommendation is what every heuristic produces and what the analyzer
aggregates. Fields are designed so the LLM can both display them to a
human (`message`) and act on them programmatically (`suggested_fix`,
`issue_type`).
"""

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional


Severity = Literal["low", "med", "high"]


@dataclass
class Recommendation:
    issue_type: str
    severity: Severity
    step_index: int
    message: str
    suggested_fix: str

    # Optional fields — heuristics fill these when applicable.
    step_range: Optional[tuple[int, int]] = None
    affected_wells: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """JSON-serializable dict for the MCP transport layer."""
        d = asdict(self)
        if d["step_range"] is None:
            d.pop("step_range")
        if not d["affected_wells"]:
            d.pop("affected_wells")
        if not d["metadata"]:
            d.pop("metadata")
        return d


def summarize(recs: list[Recommendation]) -> str:
    """One-line severity summary for the LLM."""
    if not recs:
        return "No optimization issues detected."
    counts = {"high": 0, "med": 0, "low": 0}
    for r in recs:
        counts[r.severity] += 1
    return (
        f"{counts['high']} high, {counts['med']} med, "
        f"{counts['low']} low severity issue(s) found."
    )
