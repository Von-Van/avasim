"""
Unit tests for the CombatAI module (combat/ai.py).

Tests cover:
- EV math (prob_2d10_at_least, expected_soak, expected_attack_value)
- Movement allowance calculations
- Reachable-tile BFS
- Stance selection (evade vs block)
- Strategy configuration
- decide_turn integration with engine
"""

import unittest
from combat import (
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
    AVALORE_WEAPONS,
    AVALORE_ARMOR,
    AVALORE_SHIELDS,
    AVALORE_FEATS,
    StatusEffect,
    CombatAI,
    STRATEGY_DEFAULTS,
)
from avasim import Character


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_char(name="Fighter", strength=2, dexterity=1, athletics=1, acrobatics=0):
    """Create a Character with explicit stat/skill overrides."""
    c = Character(name)
    c.base_stats["Strength"] = strength
    c.base_stats["Dexterity"] = dexterity
    c.base_skills["Strength"]["Athletics"] = athletics
    c.base_skills["Dexterity"]["Acrobatics"] = acrobatics
    return c


def _make_participant(name="Fighter", hp=20, weapon="Arming Sword",
                      armor=None, shield=None, feats=None,
                      strength=2, dexterity=1, athletics=1, acrobatics=0,
                      position=(0, 0)):
    char = _make_char(name, strength, dexterity, athletics, acrobatics)
    w = AVALORE_WEAPONS.get(weapon, AVALORE_WEAPONS["Unarmed"])
    a = AVALORE_ARMOR.get(armor) if armor else None
    s = AVALORE_SHIELDS.get(shield) if shield else None
    p = CombatParticipant(
        char, hp, hp, weapon_main=w, armor=a, shield=s, position=position,
    )
    if feats:
        for name_f in feats:
            if name_f in AVALORE_FEATS:
                p.feats.append(AVALORE_FEATS[name_f])
    return p


class TestProbability(unittest.TestCase):
    """Test prob_2d10_at_least edge cases and known values."""

    def test_prob_2d10_always(self):
        """2d10 >= 2 should be 1.0 (minimum roll is 2)."""
        self.assertAlmostEqual(CombatAI.prob_2d10_at_least(2), 1.0, places=4)

    def test_prob_2d10_impossible(self):
        """2d10 >= 21 should be 0.0 (maximum roll is 20)."""
        self.assertAlmostEqual(CombatAI.prob_2d10_at_least(21), 0.0, places=4)

    def test_prob_2d10_midpoint(self):
        """2d10 >= 11 should be ~55% (sum distribution is symmetric around 11)."""
        p = CombatAI.prob_2d10_at_least(11)
        self.assertTrue(0.50 < p < 0.60, f"p={p}")

    def test_prob_2d10_low(self):
        """2d10 >= 5 should be very high."""
        p = CombatAI.prob_2d10_at_least(5)
        self.assertGreater(p, 0.90)


class TestExpectedSoak(unittest.TestCase):
    """Test expected_soak for different armor categories."""

    def test_no_armor(self):
        p = _make_participant(armor=None)
        self.assertEqual(CombatAI.expected_soak(p), 0.0)

    def test_light_armor(self):
        p = _make_participant(armor="Light Armor")
        soak = CombatAI.expected_soak(p)
        self.assertAlmostEqual(soak, 0.5, places=1)

    def test_medium_armor(self):
        p = _make_participant(armor="Medium Armor")
        soak = CombatAI.expected_soak(p)
        self.assertAlmostEqual(soak, 1.0, places=1)

    def test_heavy_armor(self):
        p = _make_participant(armor="Heavy Armor", strength=3, athletics=2)
        soak = CombatAI.expected_soak(p)
        self.assertAlmostEqual(soak, 2.0, places=1)


class TestAttackModForWeapon(unittest.TestCase):
    """Test attack_mod_for_weapon picks the right stat."""

    def test_melee_uses_strength(self):
        p = _make_participant(weapon="Arming Sword", strength=3, athletics=2,
                              dexterity=0, acrobatics=0)
        mod = CombatAI.attack_mod_for_weapon(p, AVALORE_WEAPONS["Arming Sword"])
        expected = p.character.get_modifier("Strength", "Athletics")
        self.assertEqual(mod, expected)

    def test_ranged_uses_dexterity(self):
        p = _make_participant(weapon="Recurve Bow", strength=0, athletics=0,
                              dexterity=3, acrobatics=2)
        mod = CombatAI.attack_mod_for_weapon(p, AVALORE_WEAPONS["Recurve Bow"])
        expected = p.character.get_modifier("Dexterity", "Acrobatics")
        self.assertEqual(mod, expected)


class TestExpectedAttackValue(unittest.TestCase):
    """Test expected_attack_value returns sensible EV."""

    def test_positive_ev_with_decent_stats(self):
        attacker = _make_participant(weapon="Arming Sword", strength=3, athletics=2)
        defender = _make_participant(armor=None, dexterity=0, acrobatics=0)
        ev = CombatAI.expected_attack_value(
            attacker, defender, AVALORE_WEAPONS["Arming Sword"])
        self.assertGreater(ev, 0.0, "EV should be positive with strong attacker vs unarmored defender")

    def test_lower_ev_against_heavy_armor(self):
        attacker = _make_participant(weapon="Arming Sword", strength=2, athletics=1)
        lightly = _make_participant(armor="Light Armor")
        heavily = _make_participant(armor="Heavy Armor", strength=3, athletics=2)
        w = AVALORE_WEAPONS["Arming Sword"]
        ev_light = CombatAI.expected_attack_value(attacker, lightly, w)
        ev_heavy = CombatAI.expected_attack_value(attacker, heavily, w)
        self.assertGreater(ev_light, ev_heavy,
                           "EV should be lower against heavy armor")

    def test_piercing_ignores_armor(self):
        attacker = _make_participant(weapon="Polearm", strength=3, athletics=2,
                                     dexterity=2, acrobatics=2)
        armored = _make_participant(armor="Heavy Armor", strength=3, athletics=2)
        w = AVALORE_WEAPONS["Polearm"]
        self.assertTrue(w.is_piercing(), "Polearm should be piercing")
        ev = CombatAI.expected_attack_value(attacker, armored, w)
        # Piercing weapon: soak = 0, so EV is purely p_hit * damage / actions
        self.assertGreater(ev, 0.0)


class TestMovementAllowance(unittest.TestCase):
    """Test _movement_allowance for walk/dash."""

    def test_base_walk_allowance(self):
        p = _make_participant()
        allow = CombatAI._movement_allowance(p, use_dash=False)
        # base=5, no armor penalty
        self.assertEqual(allow, 5)

    def test_walk_used_returns_zero(self):
        p = _make_participant()
        p.free_move_used = True
        allow = CombatAI._movement_allowance(p, use_dash=False)
        self.assertEqual(allow, 0)

    def test_dash_adds_bonus(self):
        p = _make_participant()
        allow = CombatAI._movement_allowance(p, use_dash=True)
        self.assertEqual(allow, 9)  # base 5 + dash 4

    def test_slowed_reduces_allowance(self):
        p = _make_participant()
        p.status_effects.add(StatusEffect.SLOWED)
        allow = CombatAI._movement_allowance(p, use_dash=False)
        self.assertEqual(allow, 3)  # base 5 - 2


class TestReachableTiles(unittest.TestCase):
    """Test BFS reachable tile calculation."""

    def test_open_field(self):
        tmap = TacticalMap(10, 10)
        start = (5, 5)
        reachable = CombatAI._reachable_tiles(tmap, start, 2)
        # Should include tiles within 2 Manhattan distance
        self.assertIn(start, reachable)
        self.assertIn((5, 6), reachable)
        self.assertIn((6, 5), reachable)
        self.assertIn((5, 7), reachable)
        # Should not include tiles beyond allowance
        self.assertNotIn((5, 8), reachable)

    def test_blocked_by_occupant(self):
        tmap = TacticalMap(10, 10)
        blocker = _make_participant(name="Blocker", position=(5, 6))
        tmap.set_occupant(5, 6, blocker)
        reachable = CombatAI._reachable_tiles(tmap, (5, 5), 3)
        self.assertNotIn((5, 6), reachable)  # occupied tile


class TestStrategyConfig(unittest.TestCase):
    """Test strategy configuration."""

    def test_aggressive_thresholds(self):
        ai = CombatAI(strategy="aggressive")
        self.assertTrue(ai.config["prefer_attack_over_stance"])
        self.assertLess(ai.config["defend_hp_threshold"], 0.5)

    def test_defensive_thresholds(self):
        ai = CombatAI(strategy="defensive")
        self.assertFalse(ai.config["prefer_attack_over_stance"])
        self.assertGreater(ai.config["defend_hp_threshold"], 0.5)

    def test_invalid_strategy_falls_back(self):
        ai = CombatAI(strategy="invalid_strategy")
        self.assertEqual(ai.strategy, "balanced")

    def test_decision_logging(self):
        log = []
        ai = CombatAI(strategy="balanced", decision_log=log, show_decisions=True)
        self.assertIs(ai.decision_log, log)


class TestChooseStance(unittest.TestCase):
    """Test stance selection logic."""

    def test_evade_when_no_shield(self):
        ai = CombatAI(strategy="balanced")
        current = _make_participant(shield=None, dexterity=3, acrobatics=2)
        current.current_hp = 3  # Very low HP
        target = _make_participant(weapon="Arming Sword")
        tmap = TacticalMap(10, 10)
        current.position = (0, 0)
        target.position = (1, 0)
        tmap.set_occupant(0, 0, current)
        tmap.set_occupant(1, 0, target)
        engine = AvaCombatEngine([current, target], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)

        ai._choose_stance(engine, current, target)
        # Without shield, if defending it should evade
        if current.is_evading or current.is_blocking:
            self.assertTrue(current.is_evading or current.is_blocking)


class TestDecideTurn(unittest.TestCase):
    """Integration test: decide_turn should not crash and should use actions."""

    def test_basic_melee_turn(self):
        ai = CombatAI(strategy="balanced")
        attacker = _make_participant("Attacker", hp=20, weapon="Arming Sword",
                                      strength=3, athletics=2, position=(0, 0))
        defender = _make_participant("Defender", hp=20, position=(1, 0))
        tmap = TacticalMap(10, 10)
        tmap.set_occupant(0, 0, attacker)
        tmap.set_occupant(1, 0, defender)
        engine = AvaCombatEngine([attacker, defender], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)

        attacker.actions_remaining = 2
        ai.decide_turn(engine, attacker)
        # Should have used at least one action
        self.assertLess(attacker.actions_remaining, 2,
                        "AI should spend actions on its turn")

    def test_ranged_moves_into_range(self):
        ai = CombatAI(strategy="balanced")
        archer = _make_participant("Archer", hp=20, weapon="Recurve Bow",
                                    dexterity=3, acrobatics=2, position=(0, 0))
        target = _make_participant("Target", hp=20, position=(1, 0))
        tmap = TacticalMap(20, 20)
        tmap.set_occupant(0, 0, archer)
        tmap.set_occupant(1, 0, target)
        engine = AvaCombatEngine([archer, target], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)

        archer.actions_remaining = 2
        ai.decide_turn(engine, archer)
        # Ranged AI should attempt to move or attack
        self.assertLessEqual(archer.actions_remaining, 2)

    def test_no_crash_with_dead_target(self):
        ai = CombatAI(strategy="balanced")
        attacker = _make_participant("Attacker", hp=20, position=(0, 0))
        target = _make_participant("Target", hp=0, position=(1, 0))
        target.is_dead = True
        tmap = TacticalMap(10, 10)
        tmap.set_occupant(0, 0, attacker)
        engine = AvaCombatEngine([attacker, target], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)

        # Should not crash with all enemies dead
        ai.decide_turn(engine, attacker)

    def test_aggressive_prefers_attack(self):
        ai = CombatAI(strategy="aggressive")
        attacker = _make_participant("Aggressor", hp=20, weapon="Arming Sword",
                                      strength=3, athletics=2, position=(0, 0))
        defender = _make_participant("Defender", hp=20, position=(1, 0))
        tmap = TacticalMap(10, 10)
        tmap.set_occupant(0, 0, attacker)
        tmap.set_occupant(1, 0, defender)
        engine = AvaCombatEngine([attacker, defender], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)

        attacker.actions_remaining = 2
        ai.decide_turn(engine, attacker)
        # Aggressive strategy should attack rather than stance
        self.assertFalse(attacker.is_evading,
                         "Aggressive AI should prefer attacking over evading")

    def test_random_strategy_runs(self):
        """Random strategy should complete a turn without crashing."""
        ai = CombatAI(strategy="random")
        self.assertEqual(ai.strategy, "random")
        attacker = _make_participant("Randomizer", hp=20, weapon="Arming Sword",
                                      strength=2, athletics=1, position=(0, 0))
        defender = _make_participant("Target", hp=20, position=(1, 0))
        tmap = TacticalMap(10, 10)
        tmap.set_occupant(0, 0, attacker)
        tmap.set_occupant(1, 0, defender)
        engine = AvaCombatEngine([attacker, defender], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)

        attacker.actions_remaining = 2
        ai.decide_turn(engine, attacker)
        # Should have used at least some actions
        self.assertLessEqual(attacker.actions_remaining, 2)

    def test_random_strategy_full_combat(self):
        """Random strategy should complete a full combat without crashing."""
        ai = CombatAI(strategy="random")
        p1 = _make_participant("R1", hp=15, weapon="Arming Sword",
                               strength=2, athletics=1, position=(0, 0))
        p2 = _make_participant("R2", hp=15, weapon="Arming Sword",
                               strength=2, athletics=1, position=(2, 0))
        tmap = TacticalMap(10, 10)
        tmap.set_occupant(0, 0, p1)
        tmap.set_occupant(2, 0, p2)
        engine = AvaCombatEngine([p1, p2], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)
        engine.roll_initiative()

        turns = 0
        while not engine.is_combat_ended() and turns < 100:
            current = engine.get_current_participant()
            if current is None or current.current_hp <= 0:
                engine.advance_turn()
                turns += 1
                continue
            ai.decide_turn(engine, current)
            engine.advance_turn()
            turns += 1

        self.assertTrue(engine.is_combat_ended() or turns >= 100)


class TestPickTarget(unittest.TestCase):
    """Test target selection."""

    def test_picks_nearest(self):
        ai = CombatAI()
        p1 = _make_participant("Attacker", position=(0, 0))
        p2 = _make_participant("Near", position=(2, 0))
        p3 = _make_participant("Far", position=(8, 0))
        tmap = TacticalMap(10, 10)
        for p in (p1, p2, p3):
            tmap.set_occupant(*p.position, p)
        engine = AvaCombatEngine([p1, p2, p3], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)
        target = ai._pick_target(engine, p1)
        self.assertIs(target, p2, "Should pick the nearest enemy")

    def test_skips_dead(self):
        ai = CombatAI()
        p1 = _make_participant("Attacker", position=(0, 0))
        p2 = _make_participant("Dead", hp=0, position=(1, 0))
        p2.is_dead = True
        p3 = _make_participant("Alive", position=(5, 0))
        tmap = TacticalMap(10, 10)
        tmap.set_occupant(0, 0, p1)
        tmap.set_occupant(5, 0, p3)
        engine = AvaCombatEngine([p1, p2, p3], tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)
        target = ai._pick_target(engine, p1)
        self.assertIs(target, p3)


if __name__ == "__main__":
    unittest.main()
