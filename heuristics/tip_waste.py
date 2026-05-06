"""
heuristics/tip_waste.py
=======================
Detect tips dropped between consecutive aspirations from the same source.

A wasteful tip change is one where the source well of two surrounding
aspirations is identical — meaning the tip was contaminated only by liquid
it was about to re-aspirate, so dropping it added no contamination benefit.

Severity: medium (wastes plastic and time, doesn't break the protocol).
"""

from typing import Any

from ..recommendation import Recommendation


def detect(protocol: Any, snapshots: Any) -> list[Recommendation]:
    steps = protocol.steps
    waste_runs: list[dict] = []   # accumulates {start_step, end_step, source, drops}
    current_run: dict | None = None
    last_aspirate: tuple[str, str] | None = None  # (slot, well)

    for step in steps:
        if step.action == "aspirate":
            source = (step.slot, step.well)

            # If a tip was dropped/picked up between this and the previous
            # aspirate AND the source is the same, it's wasteful.
            if last_aspirate == source and current_run is not None:
                current_run["drops"] += 1
                current_run["end_step"] = step.step_index

            elif last_aspirate == source:
                # Started a new wasteful run.
                current_run = {
                    "start_step": step.step_index,
                    "end_step": step.step_index,
                    "source_slot": step.slot,
                    "source_well": step.well,
                    "drops": 1,
                }
                waste_runs.append(current_run)

            else:
                # Different source — close any open run.
                current_run = None

            last_aspirate = source

        elif step.action == "drop_tip":
            # If we're between two aspirates of the same source, the next
            # aspirate iteration will increment drops. Nothing to do here.
            pass

    return [_run_to_recommendation(r) for r in waste_runs if r["drops"] >= 2]


def _run_to_recommendation(run: dict) -> Recommendation:
    drops = run["drops"]
    return Recommendation(
        issue_type="tip_waste",
        severity="med",
        step_index=run["start_step"],
        step_range=(run["start_step"], run["end_step"]),
        message=(
            f"{drops} tip changes between aspirations from the same source "
            f"({run['source_slot']}/{run['source_well']})."
        ),
        suggested_fix=(
            f"Replace the per-iteration pick_up_tip / drop_tip pair with a "
            f"single pick_up_tip before the loop and a single drop_tip after. "
            f"Use new_tip='never' on the transfer call. Saves ~{drops} tips."
        ),
        metadata={"tips_saved": drops},
    )
