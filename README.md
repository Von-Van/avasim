<p align="center">
  <img src="assets/avasim.png" width="160" alt="AvaSim logo" />
</p>

# AvaSim - Avalore Combat Simulator

A desktop combat sandbox for the Avalore tabletop RPG. Build combatants, run AI or manual turns, and inspect detailed decision math on a tactical grid.

**Jump to:** [Screenshots](#screenshots) · [Key Features](#key-features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Project Status](#project-status)

**Screenshots**

![Combat replay with decision math and the action log](docs/screenshots/combat-log.png)

![Status panel after a duel: HP, armor, anima, and conditions](docs/screenshots/status-panel.png)

![Character setup with stats, skills, feats, and the spellbook](docs/screenshots/character-setup.png)

Screenshots are captured from the real app (`python scripts/capture_screenshots.py`).

**Key Features**

- Full Avalore action economy with a unified "one Limited action per turn" budget shared by feats and maneuvers
- All **100 feats** from [avalore.net/feats](https://avalore.net/feats) cataloged (59 engine-wired); weapon, armor, shield, and improvised-equipment resolution
- All **217 Grimoire spells** from [avalore.net/grimoire](https://avalore.net/grimoire) cataloged (30 combat-wired) with canonical casting: DC 10, anima pools, free critical casts, primary-discipline bonuses, overcast consequences, and the magic-wheel learning restriction
- Maneuvers (Grapple, Disarm, Struggle, Shove, Topple, Pull) and the Prone/Grappled/Immobilized conditions, including the per-grappler aim bonus
- Critical → Death Save → Bleedout chain with stabilization and half-movement crawl, plus stealth Sneak Attacks
- Tactical grid map with terrain, movement penalties, and range overlays
- Scenario builder for placing terrain and units with save/load
- Decision math drawer with EV logging and action traceability
- Replay timeline with per-action snapshots
- Deterministic pure-Python analysis API for single runs, batches, and paired loadout comparisons
- Export combat logs to HTML and CSV

**Quick Start**

```bash
pip install -r requirements.txt
python3 pyside_app.py
```

**Tests**

```bash
python3 -m unittest -v
make benchmark-analysis
```

**Architecture**

- `combat/contracts.py`: versioned analysis request/result dataclasses
- `combat/runtime.py`: canonical `run`, `run_batch`, and `compare` APIs
- `combat/factory.py`: pure build/scenario conversion without Qt widgets
- `data/avalore/v1/`: versioned JSON catalogs for static rules data
- `combat/engine.py`: core combat engine and turn resolution
- `combat/participant.py`: character state and action economy tracking
- `combat/items.py`: weapons, armor, shields, traits
- `combat/feats.py`: all 100 feat definitions (source of truth; exported to `data/avalore/v1/feats.json`)
- `combat/feat_handlers.py`: typed feat-effect handlers dispatched by the engine
- `combat/spells.py`: all 217 Grimoire spells with the combat-mechanics overlay (source of truth; exported to `data/avalore/v1/spells.json`)
- `ui/`: Qt widgets and tactical map rendering
- `pyside_app.py`: desktop application entry point and UI wiring

**Project Status**

- The PySide desktop app and Python combat engine are canonical.
- The TypeScript orchestrator, Rust service, Docker stack, and schema package are frozen experimental reference work until the Python runtime contract is stable.
- Spellcasting is fully enabled: the character editor has a spellbook (with primary discipline), the AI casts when a spell beats a weapon swing, and manual turns support Cast actions.
- The focus is on reproducible analysis, rules fidelity, combat visualization, and AI transparency.

**Packaging**

Desktop builds use PyInstaller (Windows-oriented version metadata in `packaging/version.txt`):

```bash
pip install pyinstaller
pyinstaller packaging/avasim.spec
```

The spec bundles the versioned rule catalogs (`data/avalore/v1`), optional fantasy fonts
(`ui/fonts`), and app assets; `combat/catalog.py` resolves catalog paths inside frozen
bundles automatically.

**Docs**

Rules references and design notes live in `docs/`:

- [`docs/mechanics_reference.md`](docs/mechanics_reference.md) — canonical combat mechanics and an implementation-coverage matrix
- [`docs/feats_catalog.md`](docs/feats_catalog.md) — all 100 feats by category with effect text and engine-wired status
- [`docs/spells_catalog.md`](docs/spells_catalog.md) — all 217 Grimoire spells by discipline and tier with engine-wired status
- [`docs/analysis_core.md`](docs/analysis_core.md) — the current canonical analysis direction

The feat and spell catalogs are the data in `combat/feats.py` / `combat/spells.py` (exported to
`data/avalore/v1/`); refresh the scraped sources of truth with `python scripts/fetch_feats.py` and
`python scripts/fetch_spells.py`, and regenerate the spell document with
`python scripts/generate_spells_doc.py`.
