# AvaSim Phase 0: Success Criteria & Metrics

## Goals

1. **Establish behavioral baseline**: Lock down current Python engine behavior before architectural changes
2. **Enable deterministic testing**: Add seeding to RNG for reproducible scenarios
3. **Create regression safety net**: Prevent behavior drift during the Rust port

## Non-Goals

1. **Performance optimization**: Phase 0 is about correctness, not speed
2. **New features**: No new feats, weapons, or combat mechanics
3. **UI changes**: Desktop app remains as-is during this phase
4. **Architecture changes**: No containerization, services, or language ports yet

## Success Metrics

### Correctness
- ✅ **10 deterministic fixture scenarios** captured with fixed seeds and expected outcomes
- ✅ **All fixtures pass** in current Python engine (baseline established)
- ✅ **CI integration** runs fixtures on every commit
- ✅ **Zero tolerance** for behavior drift (tests fail if outcomes change)

### Determinism
- ✅ **Seed control**: Combat engine accepts optional RNG seed
- ✅ **Same seed = same outcome**: Identical inputs produce identical results
- ✅ **Documented**: Fixture format and expected outcomes are human-readable

### Coverage (Fixture Diversity)
- ✅ At least one fixture for each category:
  1. Basic melee combat (hit/miss/damage)
  2. Ranged combat with line-of-sight
  3. Movement and opportunity attacks
  4. Status effects (SLOWED, PRONE, etc.)
  5. Feat-driven mechanics (Hamstring, Control, Mighty Strike)
  6. Multi-round combat sequence
  7. Terrain interactions (cover, walls, forest)
  8. Complex feat combos (Patient Flow, Dueling Stance)
  9. Knockback and forced movement
  10. Full combat from initiative to defeat

### Deployability
- ✅ **One-command test run**: `make test-baseline` or `pytest test_baseline.py`
- ✅ **CI ready**: Fixtures run in GitHub Actions (or equivalent)
- ✅ **Fast execution**: All 10 fixtures complete in under 10 seconds

## Definition of Done

Phase 0 is complete when:

1. ✅ `docs/phase0_success_criteria.md` exists (this file)
2. ✅ `combat/dice.py` supports seeding via `set_seed()`
3. ✅ `tests/fixtures/` contains 10 JSON/YAML scenario files with:
   - Input state (characters, positions, seeds)
   - Expected output (final HP, positions, status effects)
4. ✅ `test_baseline.py` loads fixtures and asserts outcomes
5. ✅ All baseline tests pass locally
6. ✅ CI pipeline includes baseline tests and passes

## Rollback Strategy

If Phase 0 changes cause issues:
- Revert `combat/dice.py` changes (remove seeding)
- Delete `test_baseline.py` and `tests/fixtures/`
- Continue with existing `test_combat.py` suite

## Next Phase Gate

Do NOT proceed to Phase 1 (Containerized Foundation) until:
- All Phase 0 success criteria are met
- At least one other human or AI has reviewed the fixtures
- CI passes with baseline tests enabled
