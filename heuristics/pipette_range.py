"""
heuristics/pipette_range.py
===========================
Detect aspirate / dispense volumes outside the pipette's working range.

The simulation log doesn't directly state the pipette's min/max — but the
loaded tip rack's nominal volume is a strong proxy:

    P10  → 10 µL tips     (range  1–10 µL)
    P20  → 20 µL tips     (range  1–20 µL)
    P50  → 50 µL tips     (range  5–50 µL)
    P200 → 200 µL tips    (range 20–200 µL)
    P300 → 300 µL tips    (range 20–300 µL)
    P1000 → 1000 µL tips  (range 100–1000 µL)

If a transfer asks for less than 10% of the rack's max, we flag it as
likely below the pipette's accurate range.

Severity: high (produces measurably wrong volumes).
"""

import re
from typing import Any

from ..recommendation import Recommendation


# (substring in tiprack name, min_uL, max_uL)
_TIPRACK_RANGES: list[tuple[str, float, float]] = [
    ("10ul",   1.0,    10.0),
    ("20ul",   1.0,    20.0),
    ("50ul",   5.0,    50.0),
    ("200ul",  20.0,  200.0),
    ("300ul",  20.0,  300.0),
    ("1000ul", 100.0, 1000.0),
]


def _infer_pipette_range(slot_labware: dict) -> tuple[float, float] | None:
    """Pick the largest tiprack found and return its (min, max) range."""
    best: tuple[float, float] | None = None
    for lw_name in slot_labware.values():
        lw_lower = re.sub(r"\s+", "", lw_name.lower())
        for hint, lo, hi in _TIPRACK_RANGES:
            if hint in lw_lower:
                if best is None or hi > best[1]:
                    best = (lo, hi)
    return best


def detect(protocol: Any, snapshots: Any) -> list[Recommendation]:
    rng = _infer_pipette_range(protocol.slot_labware)
    if rng is None:
        return []   # can't infer pipette → can't check
    lo, hi = rng

    out: list[Recommendation] = []
    for step in protocol.steps:
        if step.action not in ("aspirate", "dispense"):
            continue
        v = step.volume_ul
        if v is None:
            continue

        if v < lo:
            out.append(_make_rec(step, v, lo, hi, "below"))
        elif v > hi:
            out.append(_make_rec(step, v, lo, hi, "above"))

    return out


def _make_rec(step, v: float, lo: float, hi: float, side: str) -> Recommendation:
    direction = "below the minimum" if side == "below" else "above the maximum"
    bound = lo if side == "below" else hi
    return Recommendation(
        issue_type="pipette_range",
        severity="high",
        step_index=step.step_index,
        message=(
            f"Step {step.step_index}: {step.action} of {v:.1f} µL is "
            f"{direction} accurate range ({lo:.1f}–{hi:.1f} µL)."
        ),
        suggested_fix=(
            f"Adjust the volume to within {lo:.1f}–{hi:.1f} µL, or load a "
            f"different pipette/tiprack capable of {v:.1f} µL."
        ),
        metadata={
            "volume_uL": v,
            "pipette_min": lo,
            "pipette_max": hi,
            "violated_bound": bound,
        },
    )
