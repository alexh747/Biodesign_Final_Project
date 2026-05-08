# Optimization and Error Checking

Member 4 module for the Biodesign Automation final project (Spring 2026).

Reads Opentrons simulation log text, runs a suite of heuristic detectors,
and returns a structured list of recommendations the LLM can act on. Each
recommendation carries a severity, a step index, a human-readable message,
and a concrete suggested fix.

## How it fits in the team pipeline

```
Member 1 (generate)  →  Member 2 (simulate)  →  Member 4 (THIS module)  →  Member 3 (visualize)
                                                       │
                                                       ▼
                                          Member 5 (MCP server) → LLM
```

Consumes the `logs` string from Member 2's `run_opentrons_simulation()`,
parses it via Member 3's `parse_log()` and `build_snapshots()`, and emits a
JSON-ready dict that Member 5 hands to the LLM.

Target experiments: dilutions, PCR, Illumina prep (RT normalization).

## Quick start

CLI mode, from the **Final Project root** (not from inside this folder):

```bash
python -m OptimizationAndErrorChecking.analyzer <path-to-log>
```

Library mode (this is what Member 5's MCP server does):

```python
from OptimizationAndErrorChecking.analyzer import analyze_optimization

result = analyze_optimization(simulation_logs="<raw log text>")
```

## Folder layout

```
OptimizationAndErrorChecking/
├── analyzer.py          # orchestrator + CLI entry point
├── recommendation.py    # Recommendation dataclass + summarize() helper
├── heuristics/          # six detectors — see heuristics/README.md
└── test_protocols/      # deliberately-bad protocols, one per heuristic — see test_protocols/README.md
```

## Output shape

`analyze_optimization()` always returns a dict with these six keys:

```json
{
  "status": "success" | "error",
  "protocol_name": "PCR Setup - Master Mix and Template",
  "step_count": 49,
  "recommendations": [
    {
      "issue_type": "batchable_transfers",
      "severity": "low",
      "step_index": 1,
      "message": "8 aspirations from 2/A1 could be combined into one 144 µL aspirate + 8 dispenses.",
      "suggested_fix": "Replace the 8 transfer() calls with a single distribute()...",
      "step_range": [1, 16],
      "metadata": {"chain_length": 8, "total_volume_uL": 144.0}
    }
  ],
  "summary": "0 high, 0 med, 1 low severity issue(s) found.",
  "error_detail": ""
}
```

Severity values are `"high"`, `"med"`, or `"low"`. Recommendations are
sorted high-severity first, then by step index ascending.

## Status

v1 — six heuristics implemented, three confirmed working on real logs
(`tip_waste`, `volume_overflow`, `batchable_transfers`). Three currently
silent or partially blocked; see [heuristics/README.md](heuristics/README.md)
for the v2 todo list.
