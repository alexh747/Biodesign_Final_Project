"""
heuristics/empty_aspirate.py
============================
Detect aspirations that pull more liquid than is currently in the well.

If a protocol asks for 100 µL but the well only has 30 µL, the pipette
either grabs air or fails outright. This usually means the user forgot to
declare an initial volume (via `# INIT` directive) or made a math error
when computing transfer volumes.

Severity: high (produces wrong results or runtime failures).
"""

from typing import Any

from ..recommendation import Recommendation


# Reservoirs and trash are excluded by Member 3's tracker; they have
# slot_max_volumes of 0 or inf. Aspirate-from-zero on a tracked well is
# the signal we care about.
_EPSILON = 0.5  # µL


def detect(protocol: Any, snapshots: Any) -> list[Recommendation]:
    out: list[Recommendation] = []

    # Build a quick lookup: snapshot at each step_index = state AFTER step.
    # We'll need state BEFORE the aspirate, so pair each aspirate step with
    # the snapshot whose step_index is one less.
    snap_by_idx = {s.step_index: s for s in snapshots}

    for step in protocol.steps:
        if step.action != "aspirate":
            continue

        # Reservoirs / trash: skip
        max_vol = protocol.slot_max_volumes.get(step.slot, 0)
        if max_vol == 0 or max_vol == float("inf"):
            continue

        prior = snap_by_idx.get(step.step_index - 1)
        if prior is None:
            continue

        available = prior.well_volumes.get((step.slot, step.well), 0.0)
        requested = step.volume_ul or 0.0

        if requested > available + _EPSILON:
            out.append(
                Recommendation(
                    issue_type="empty_aspirate",
                    severity="high",
                    step_index=step.step_index,
                    message=(
                        f"Step {step.step_index}: aspirating {requested:.1f} µL from "
                        f"{step.slot}/{step.well}, but only {available:.1f} µL is "
                        f"available."
                    ),
                    suggested_fix=(
                        f"Either declare an initial volume for {step.slot}/{step.well} "
                        f"with a `# INIT slot {step.slot} {step.well} <volume>uL` "
                        f"directive, or reduce the requested aspirate to at most "
                        f"{available:.1f} µL."
                    ),
                    affected_wells=[step.well],
                    metadata={
                        "slot": step.slot,
                        "requested_uL": requested,
                        "available_uL": available,
                    },
                )
            )

    return out
