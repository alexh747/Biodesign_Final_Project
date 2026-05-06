"""
analyzer.py
===========
Orchestrator for the optimization & error-checking module.

Takes raw Opentrons simulation log text, parses it via Member 3's visualizer
package, runs every heuristic detector, and aggregates the results into a
single MCP-ready dict.

CLI usage:
    python -m OptimizationAndErrorChecking.analyzer <path-to-log>
"""

import json
import os
import sys
from typing import Any

# ── Visualizer import (Member 3's package) ────────────────────────────────────
# The visualizer currently lives at:
#   Final Project/Visualization/FOR ALEX AND JOSH ON VISUALIZATION/visualizer/
# This path manipulation is a v1 workaround. When the team agrees on a flat
# project layout (or pip-installs the visualizer), this block goes away.
_HERE = os.path.dirname(os.path.abspath(__file__))
_VIZ_PARENT = os.path.normpath(
    os.path.join(_HERE, "..", "Visualization", "FOR ALEX AND JOSH ON VISUALIZATION")
)
if _VIZ_PARENT not in sys.path:
    sys.path.insert(0, _VIZ_PARENT)

# Import directly from submodules to skip the package __init__, which pulls
# in matplotlib / numpy / Pillow that the analyzer doesn't need.
from visualizer.log_parser import parse_log         # noqa: E402
from visualizer.state_tracker import build_snapshots  # noqa: E402

# ── Local package imports ────────────────────────────────────────────────────
from .recommendation import Recommendation, summarize
from .heuristics import (
    tip_waste,
    volume_overflow,
    empty_aspirate,
    pipette_range,
    batchable_transfers,
    tip_rack_exhaustion,
)


_DETECTORS = (
    tip_waste,
    volume_overflow,
    empty_aspirate,
    pipette_range,
    batchable_transfers,
    tip_rack_exhaustion,
)


def analyze_optimization(simulation_logs: str) -> dict:
    """
    Run all heuristics against simulation logs.

    Returns
    -------
    dict with keys:
        status              : "success" | "error"
        protocol_name       : str   (parsed from logs, "Unnamed Protocol" if absent)
        step_count          : int   (number of parsed pipetting steps)
        recommendations     : list[dict]  (one Recommendation.to_dict() per finding,
                                           sorted high → low severity, then by step)
        summary             : str   (one-line severity summary for the LLM)
        error_detail        : str   (empty on success)
    """
    if not simulation_logs or not isinstance(simulation_logs, str):
        return _error("simulation_logs must be a non-empty string.")

    try:
        protocol = parse_log(simulation_logs)
        snapshots = build_snapshots(protocol)
    except Exception as exc:
        return _error(f"Failed to parse logs: {type(exc).__name__}: {exc}")

    all_recs: list[Recommendation] = []
    for detector in _DETECTORS:
        try:
            all_recs.extend(detector.detect(protocol, snapshots))
        except Exception as exc:
            # One broken heuristic shouldn't sink the rest.
            all_recs.append(
                Recommendation(
                    issue_type="heuristic_error",
                    severity="low",
                    step_index=-1,
                    message=(
                        f"Internal: heuristic {detector.__name__} raised "
                        f"{type(exc).__name__}: {exc}"
                    ),
                    suggested_fix="No protocol change required; fix the analyzer.",
                )
            )

    # Sort high severity first, then by step_index ascending.
    severity_rank = {"high": 0, "med": 1, "low": 2}
    all_recs.sort(key=lambda r: (severity_rank.get(r.severity, 3), r.step_index))

    return {
        "status": "success",
        "protocol_name": protocol.protocol_name,
        "step_count": len(protocol.steps),
        "recommendations": [r.to_dict() for r in all_recs],
        "summary": summarize(all_recs),
        "error_detail": "",
    }


def _error(detail: str) -> dict:
    return {
        "status": "error",
        "protocol_name": "",
        "step_count": 0,
        "recommendations": [],
        "summary": "",
        "error_detail": detail,
    }


# ── CLI entry point ──────────────────────────────────────────────────────────

def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "Usage: python -m OptimizationAndErrorChecking.analyzer <log_file>",
            file=sys.stderr,
        )
        return 1

    log_path = argv[1]
    if not os.path.isfile(log_path):
        print(f"Error: file not found — {log_path}", file=sys.stderr)
        return 1

    with open(log_path, encoding="utf-8") as f:
        logs = f.read()

    result = analyze_optimization(logs)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
