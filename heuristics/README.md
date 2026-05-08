# heuristics/

Six heuristic detectors that scan a parsed Opentrons protocol and emit
structured `Recommendation` objects describing problems found. The
`analyzer.py` orchestrator runs every detector here and aggregates their
output into a single MCP-ready dict.

## Common contract

Every module in this folder exposes one function with the same signature:

```python
def detect(protocol, snapshots) -> list[Recommendation]:
    ...
```

- `protocol` — Member 3's `ParsedProtocol`: typed event list, labware map,
  per-slot capacities.
- `snapshots` — Member 3's `list[DeckSnapshot]`: well volumes, tip state,
  source-aspiration tracking at each moment in the protocol.

This uniform shape is what lets `analyzer.py` iterate the detectors in a
single loop. Adding a new heuristic does not require any change to the
existing ones.

## Detectors

| File | Kind | Severity | Catches |
|---|---|---|---|
| `tip_waste.py` | Optimization | med | Tips dropped between aspirations from the same source well |
| `volume_overflow.py` | Edge case | high | Wells whose tracked volume exceeds labware capacity |
| `empty_aspirate.py` | Edge case | high | Aspirations that pull more liquid than the well currently holds |
| `pipette_range.py` | Edge case | high | Volumes outside the pipette's accurate range (inferred from tiprack) |
| `batchable_transfers.py` | Optimization | low | N aspirate-dispense pairs from same source that fit in one pipette draw |
| `tip_rack_exhaustion.py` | Edge case | high | Protocols requesting more tips than the loaded racks contain |

**Optimization** = code works, but is wasteful. Non-blocking.
**Edge case** = code may fail at runtime or produce wrong results. Blocking.

The split mirrors the module's role title: optimization *and* error checking.

## v1 known limitations

- **`tip_waste`** can be over-eager when the same well coordinate holds
  *different* liquids across the protocol — currently treats well address
  as identity. Future fix: consume `protocol.liquid_map` for true identity.
- **`pipette_range`** infers the pipette range from tiprack name substrings
  like `"300ul"`, but real Opentrons log labware names print as
  `"Opentrons OT-2 96 Tip Rack 300 µL"` (with `µ` and a space). The current
  match misses these, so this detector is silent on real logs until the
  pattern is fixed.
- **`tip_rack_exhaustion`** counts pickup events in the parsed log, but
  `opentrons_simulate` halts on the 97th pickup with `OutOfTipsError` and
  emits no further actions. The detector sees 96 ≤ 96 and stays silent on
  the very protocols it should catch. Future fix: also scan the raw log for
  `OutOfTipsError`.

## Adding a new heuristic

1. Copy an existing file as a template (e.g. `tip_waste.py`).
2. Rename it to describe what it detects.
3. Implement `detect(protocol, snapshots) -> list[Recommendation]`.
4. Import the new module in `analyzer.py` and add it to the `_DETECTORS`
   tuple — that's the only edit needed outside this folder.
