# AvaSim Analysis Core

> **Status: stable.** The request/result contracts below and the determinism
> guarantees are the supported surface for clients — the desktop UI and scripts
> today. They carry explicit `SCHEMA_VERSION` / `ENGINE_VERSION` stamps
> (`combat/contracts.py`), so a breaking change should bump those and stay
> covered by the test suite (baselines, catalog coverage, mechanics,
> spellcasting, and rules fidelity).

The canonical product runtime is the existing PySide desktop app plus the pure-Python combat engine in `combat/`.

The analysis core adds a stable boundary for reproducible decision support without porting the working engine:

- `RunRequest` / `RunResult` for one deterministic combat.
- `BatchRequest` / `BatchReport` for seed-derived Monte Carlo batches.
- `ComparisonRequest` / `ComparisonReport` for paired A/B runs using identical seed sequences.
- `ValidationIssue` for structured build and scenario validation.
- Public APIs exported from `combat`: `run`, `run_batch`, `compare`, `validate_build`, and `validate_scenario`.

Batch runs use summary capture by default to avoid replay/log overhead. Representative replay seeds are selected deterministically and rerun with replay capture when requested.

The earlier service, TypeScript schema, Rust runtime, and container work remain frozen reference material, consolidated under `archive/`. The condition that froze them — a stable, test-backed Python runtime contract — is now met; resuming any port is a deliberate, separate decision, and any such work should target this contract rather than reinvent it.

Static weapons, armor, shields, feats, and spells are defined as Python literals in `combat/items.py`, `combat/feats.py`, and `combat/spells.py` (`AVALORE_WEAPONS`, `AVALORE_FEATS`, etc.) and read directly by the engine as the single source of truth.

## Determinism

- Single runs use a run-scoped seeded RNG.
- Batch seeds are `base_seed + run_index`.
- Paired comparisons reuse the same ordered seed list for both sides.
- Core event records use deterministic sequence numbers.

## Useful Commands

```bash
python3 -m unittest -v
python scripts/benchmark_analysis.py --runs 1000
make benchmark-analysis
```
