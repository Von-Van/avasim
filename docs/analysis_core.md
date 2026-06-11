# AvaSim Analysis Core

The canonical product runtime is the existing PySide desktop app plus the pure-Python combat engine in `combat/`.

The analysis core adds a stable boundary for reproducible decision support without porting the working engine:

- `RunRequest` / `RunResult` for one deterministic combat.
- `BatchRequest` / `BatchReport` for seed-derived Monte Carlo batches.
- `ComparisonRequest` / `ComparisonReport` for paired A/B runs using identical seed sequences.
- `ValidationIssue` for structured build and scenario validation.
- Public APIs exported from `combat`: `run`, `run_batch`, `compare`, `validate_build`, and `validate_scenario`.

Batch runs use summary capture by default to avoid replay/log overhead. Representative replay seeds are selected deterministically and rerun with replay capture when requested.

The current service, TypeScript schema, Rust runtime, and container work remain frozen experimental reference material. They should not receive new feature work until this Python runtime contract is stable and test-backed.

Static weapons, armor, shields, feats, and spells are exported to versioned JSON under `data/avalore/v1/`. The Python modules still expose the same constants (`AVALORE_WEAPONS`, `AVALORE_FEATS`, etc.), now loaded back into the existing dataclasses for compatibility.

## Determinism

- Single runs use a run-scoped seeded RNG.
- Batch seeds are `base_seed + run_index`.
- Paired comparisons reuse the same ordered seed list for both sides.
- Core event records use deterministic sequence numbers.

## Useful Commands

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
python scripts/benchmark_analysis.py --runs 1000
python scripts/export_rule_catalogs.py
make benchmark-analysis
```
