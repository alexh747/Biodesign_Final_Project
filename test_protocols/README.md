# test_protocols/

Six minimal Opentrons protocols, each deliberately constructed to trigger
exactly one heuristic in the analyzer.

| File | Targets | Expected to fire? |
|---|---|---|
| `trigger_tip_waste.py` | `tip_waste` | ✅ yes (also: `batchable_transfers`) |
| `trigger_volume_overflow.py` | `volume_overflow` | ✅ yes |
| `trigger_empty_aspirate.py` | `empty_aspirate` | ✅ yes |
| `trigger_pipette_range.py` | `pipette_range` | ⚠️ blocked by known regex bug |
| `trigger_batchable_transfers.py` | `batchable_transfers` | ✅ yes |
| `trigger_tip_rack_exhaustion.py` | `tip_rack_exhaustion` | ⚠️ simulator stops at tip 97 |

## How to run a test

From the **Final Project root**:

1. Simulate the bad protocol to produce a log:
   ```bash
   ../.venv/Scripts/opentrons_simulate.exe \
     OptimizationAndErrorChecking/test_protocols/trigger_tip_waste.py \
     > /tmp/tip_waste_log.txt 2>&1
   ```
   (On Git Bash; for PowerShell adapt the redirect.)

2. Run the analyzer on the resulting log:
   ```bash
   python -m OptimizationAndErrorChecking.analyzer /tmp/tip_waste_log.txt
   ```

3. Confirm the expected heuristic appears in `recommendations`.

## What "blocked" means

Two of the six are not fully testable as-is:

- **pipette_range** — the heuristic's labware-name matching uses substrings
  like `"300ul"`, but real simulator logs print `"300 µL"`. Fix in v2.
- **tip_rack_exhaustion** — `opentrons_simulate` halts on the 97th pickup
  attempt, so the log only contains 96 pickups. The heuristic counts log
  events, sees 96 ≤ 96, and stays silent. A more robust v2 detects the
  `OutOfTipsError` line in the raw stderr.

These two are documented bugs, not silent regressions. Their failures
*confirm* the v2 todo list.
