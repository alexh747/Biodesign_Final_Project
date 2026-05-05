# Optimization and Error Checking

Member 4 module for the Biodesign Automation final project (Spring 2026).

This module consumes Opentrons simulation logs produced by the simulation engine
and emits structured, actionable recommendations the LLM can use to rewrite the
protocol. Heuristics target tip waste, redundant aspirations, suboptimal pathing,
and volume errors.

Target experiments: dilutions, PCR, Illumina prep.
