"""
heuristics/tip_waste.py
=======================
Detect tips dropped between consecutive aspirations from the same source.

A tip change is wasteful when **both** conditions hold:
  1. Two consecutive aspirations target the same (slot, well).
  2. A `drop_tip` action occurred between those two aspirations.

If condition 2 is missing, the protocol is using ONE tip for many transfers
from the same source — that's the efficient pattern, not waste. (The
batchable_transfers heuristic handles that separately.)

Severity: medium (wastes plastic and time, doesn't break the protocol).
"""

from typing import Any

from ..recommendation import Recommendation


def detect(protocol: Any, snapshots: Any) -> list[Recommendation]:
    steps = protocol.steps
    waste_runs: list[dict] = []
    current_run: dict | None = None

    last_aspirate_source: tuple[str, str] | None = None
    last_aspirate_step: int = -1
    dropped_since_last_aspirate = False

    for step in steps:
        if step.action == "aspirate":
            source = (step.slot, step.well)
            wasteful = (
                dropped_since_last_aspirate
                and last_aspirate_source == source
            )

            if wasteful:
                if current_run is None:
                    current_run = {
                        "start_step": last_aspirate_step,
                        "end_step": step.step_index,
                        "source_slot": step.slot,
                        "source_well": step.well,
                        "drops": 1,
                    }
                    waste_runs.append(current_run)
                else:
                    current_run["drops"] += 1
                    current_run["end_step"] = step.step_index
            else:
                current_run = None  # streak broken

            last_aspirate_source = source
            last_aspirate_step = step.step_index
            dropped_since_last_aspirate = False

        elif step.action == "drop_tip":
            dropped_since_last_aspirate = True

    return [_run_to_recommendation(r) for r in waste_runs]


def _run_to_recommendation(run: dict) -> Recommendation:
    drops = run["drops"]
    return Recommendation(
        issue_type="tip_waste",
        severity="med",
        step_index=run["start_step"],
        step_range=(run["start_step"], run["end_step"]),
        message=(
            f"{drops} wasteful tip change(s) between aspirations from the same "
            f"source ({run['source_slot']}/{run['source_well']})."
        ),
        suggested_fix=(
            f"Replace the per-iteration pick_up_tip / drop_tip pair with a "
            f"single pick_up_tip before the loop and a single drop_tip after. "
            f"Use new_tip='never' on the transfer call. Saves ~{drops} tips."
        ),
        metadata={"tips_saved": drops},
    )
