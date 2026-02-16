# AvaSim Baseline Fixtures

This directory contains **deterministic baseline scenarios** for the AvaSim combat engine. These fixtures are the source of truth for behavior validation during architectural changes (e.g., the Rust port).

## What are these files?

Each `.json` file represents a combat scenario with:

- **Input**: Character builds, positions, seeds, and actions to perform
- **Expected Output**: Final HP, positions, status effects, and other observable state

## How are they used?

The test suite in `test_baseline.py` loads these fixtures and re-runs the scenarios with the same seed, then asserts that outputs match exactly. If a test fails, the engine behavior has changed.

## Fixture Coverage

| Fixture | Description |
|---------|-------------|
| `01_basic_melee.json` | Basic melee attack sequence |
| `02_ranged_los.json` | Ranged combat with line of sight |
| `03_movement_oa.json` | Movement triggering opportunity attack |
| `04_status_effects.json` | Hamstring applying SLOWED status |
| `05_mighty_strike.json` | Mighty Strike knockback |
| `06_multi_round.json` | Multi-round combat with turn cycling |
| `07_terrain_cover.json` | Forest terrain cover bonus |
| `08_patient_flow.json` | Patient Flow attack redirection |
| `09_control_knockback.json` | Control knockback into wall |
| `10_full_combat.json` | Full combat from initiative to defeat |

## Regenerating Fixtures

**⚠️ WARNING**: Only regenerate fixtures when you intentionally want to update the baseline behavior.

```bash
make generate-fixtures
```

This will:
1. Run all 10 scenarios with fixed seeds
2. Capture the current engine outputs
3. Overwrite the existing `.json` files

## Rules for Fixtures

1. **Never hand-edit fixture outputs** - they must reflect actual engine behavior
2. **Never change seeds** - changing seeds invalidates the baseline
3. **Add new fixtures** when testing new features (don't replace existing ones)
4. **Version control all changes** - fixture updates are code changes

## Phase 0 Success Criteria

- ✅ 10 deterministic fixtures exist
- ✅ All fixtures pass in current Python engine
- ✅ Fixtures cover core mechanics (melee, ranged, feats, terrain, status effects)
- ✅ CI integration ready (run via `make test-baseline`)
