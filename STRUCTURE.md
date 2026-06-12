# AvaSim Project Structure

## Directory Organization

```
avasim/
├── combat/                  # Core combat engine + analysis core (canonical)
│   ├── engine.py            # Combat loop, attacks, maneuvers, spellcasting
│   ├── participant.py       # Character combat state and action economy
│   ├── items.py             # Weapons, armor, shields (+ improvised variants)
│   ├── feats.py             # All 100 avalore.net feats (source of truth)
│   ├── feat_handlers.py     # Typed feat-effect handlers dispatched by the engine
│   ├── spells.py            # All 217 Grimoire spells + combat-mechanics overlay
│   ├── ai.py                # EV-driven combat AI (attacks, feats, spellcasting)
│   ├── map.py               # Tactical grid, pathfinding, line of sight
│   ├── dice.py              # Seeded 2d10 dice (run-scoped RNG)
│   ├── enums.py             # Range bands, statuses, terrain
│   ├── contracts.py         # RunRequest/RunResult & batch/compare contracts
│   ├── runtime.py           # Canonical run / run_batch / compare APIs
│   ├── factory.py           # Build/scenario -> combat objects (no Qt)
│   ├── validation.py        # Structured build/scenario validation
│   ├── recorder.py          # Replay/event capture
│   ├── events.py            # Structured event records
│   ├── batch.py             # Monte Carlo batch aggregation
│   └── catalog.py           # Versioned JSON catalog loader
│
├── data/avalore/v1/         # Versioned JSON rule catalogs (generated)
├── docs/                    # Rules references, coverage matrix, catalogs
├── scripts/                 # Scrapers, exporters, benchmarks, doc generators
├── tests/data/              # Scraped source-of-truth fixtures (feats, spells)
├── ui/                      # PySide6 widgets, theming, tactical map rendering
├── packaging/               # PyInstaller spec + version metadata
│
├── apps/, services/,        # FROZEN experimental next-gen reference
│   packages/, infra/        # (TS orchestrator, Rust engine, schema, Docker)
│
├── avasim.py                # Character model (stats, skills, XP)
├── character.py             # Character sheet template structure
├── pyside_app.py            # Desktop application entry point
├── examples.py              # Character simulator usage examples
├── test_*.py                # Test suite (197 tests)
└── requirements.txt         # Python dependencies
```

## Key Flows

- **Rules data**: live pages → `scripts/fetch_feats.py` / `fetch_spells.py` →
  fixtures in `tests/data/` → literals in `combat/feats.py` / `combat/spells.py`
  → `scripts/export_rule_catalogs.py` → `data/avalore/v1/*.json` (loaded at
  runtime by `combat/catalog.py`).
- **Analysis**: `combat.run` / `run_batch` / `compare` (see
  `docs/analysis_core.md`) give deterministic, seed-stable results consumed by
  the UI's batch and comparison tabs.
- **Docs**: `docs/mechanics_reference.md` tracks rule coverage;
  `docs/feats_catalog.md` and `docs/spells_catalog.md` are generated from the
  catalogs.

## Adding New Features

### New combat rule
1. Ground it in the canonical pages (avalore.net/mechanics, /extended-mechanics,
   /arcane, /grimoire, /feats)
2. Implement in `combat/engine.py` / `combat/participant.py`
3. Update the coverage matrix in `docs/mechanics_reference.md`
4. Add tests (`test_combat.py`, `test_spellcasting.py`, `test_rules_fidelity.py`)

### New wired spell
1. Add a `SPELL_MECHANICS` entry in `combat/spells.py` (note simplifications)
2. Extend `engine._apply_spell_effects` only if new vocabulary is needed
3. Re-run `scripts/export_rule_catalogs.py` and `scripts/generate_spells_doc.py`
4. Add tests to `test_spellcasting.py`

### New UI component
1. Add to `ui/components.py`, export in `ui/__init__.py`
2. Wire into `pyside_app.py`
