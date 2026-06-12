"""
Action-economy and maneuver tests for the Avalore combat engine.

These lock in the canonical action economy from https://avalore.net/mechanics
and https://avalore.net/extended-mechanics:

- Two actions per turn.
- Exactly ONE Limited ability per turn, shared between feat abilities and
  maneuvers (Shove/Topple/Pull/...).
- Maneuvers: Shove/Topple/Grapple/Disarm/Struggle/Pull, with the Grappled
  condition (-3 to physical rolls, movement 0) and Prone ending grapples.
"""

import unittest
from unittest.mock import patch

import combat.engine as engine_module
from combat import (
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
    AVALORE_WEAPONS,
    AVALORE_SHIELDS,
    AVALORE_ARMOR,
    StatusEffect,
)
from avasim import Character


def _crit():
    """roll_2d10 stub forcing a critical (10,10)."""
    return (20, (10, 10))


def _fixed(total, d1, d2):
    def _inner():
        return (total, (d1, d2))
    return _inner


class ActionEconomyBase(unittest.TestCase):
    def duel(self, weapon="Unarmed"):
        a = CombatParticipant(Character("A"), 20, 20, weapon_main=AVALORE_WEAPONS[weapon])
        d = CombatParticipant(Character("D"), 20, 20, weapon_main=AVALORE_WEAPONS["Unarmed"])
        tmap = TacticalMap(20, 20)
        a.position = (0, 0)
        d.position = (1, 0)
        tmap.set_occupant(0, 0, a)
        tmap.set_occupant(1, 0, d)
        eng = AvaCombatEngine([a, d], tmap)
        a.actions_remaining = 5  # plenty of raw actions; the limited slot is the constraint
        d.actions_remaining = 5
        return eng, a, d


class TestLimitedBudget(ActionEconomyBase):
    def test_two_actions_per_turn_default(self):
        p = CombatParticipant(Character("P"), 20, 20)
        self.assertEqual(p.actions_remaining, 2)
        self.assertTrue(p.consume_action(1, action_name="a"))
        self.assertTrue(p.consume_action(1, action_name="b"))
        self.assertFalse(p.consume_action(1, action_name="c"))

    def test_one_limited_per_turn_shared_maneuvers_and_feats(self):
        eng, a, d = self.duel()
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            r1 = eng.action_shove(a, d)
        self.assertTrue(r1["used"])
        self.assertTrue(a.limited_action_used)
        # A second Limited maneuver is blocked even though actions remain.
        r2 = eng.action_topple(a, d)
        self.assertFalse(r2["used"])
        # A Limited *feat* action is likewise blocked (shared budget).
        self.assertFalse(a.consume_action(1, is_limited=True, action_name="some feat"))
        # A non-limited action is still allowed.
        self.assertTrue(a.consume_action(1, action_name="ordinary"))

    def test_limited_feat_blocks_limited_maneuver(self):
        eng, a, d = self.duel()
        self.assertTrue(a.consume_action(1, is_limited=True, action_name="feat ability"))
        r = eng.action_shove(a, d)
        self.assertFalse(r["used"])

    def test_can_use_limited_shares_flag(self):
        p = CombatParticipant(Character("P"), 20, 20)
        self.assertTrue(p.can_use_limited("FeatA"))
        self.assertTrue(p.limited_action_used)
        self.assertFalse(p.can_use_limited("FeatB"))
        self.assertFalse(p.consume_action(1, is_limited=True, action_name="x"))

    def test_per_scene_limited_respects_turn_budget(self):
        p = CombatParticipant(Character("P"), 20, 20)
        p.limited_action_used = True  # a Limited action already used this turn
        self.assertFalse(p.can_use_limited("Trick Shot", per_scene=True, limit=3))
        # The scene charge must NOT be consumed when the per-turn slot is gone.
        self.assertEqual(p.limited_used_scene_counts.get("Trick Shot", 0), 0)

    def test_start_turn_resets_budget(self):
        p = CombatParticipant(Character("P"), 20, 20)
        p.consume_action(1, is_limited=True, action_name="x")
        self.assertTrue(p.limited_action_used)
        p.start_turn()
        self.assertFalse(p.limited_action_used)
        self.assertEqual(p.actions_remaining, 2)


class TestManeuvers(ActionEconomyBase):
    def test_shove_deals_damage_and_knockback(self):
        eng, a, d = self.duel()
        hp_before = d.current_hp
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            r = eng.action_shove(a, d)
        self.assertTrue(r["success"])
        self.assertLess(d.current_hp, hp_before)  # unarmed damage applied
        self.assertNotEqual(d.position, (1, 0))   # pushed at least 2 blocks

    def test_critical_shove_knocks_prone(self):
        eng, a, d = self.duel()
        with patch.object(engine_module, "roll_2d10", _crit):
            r = eng.action_shove(a, d)
        self.assertTrue(r["success"])
        self.assertTrue(d.has_status(StatusEffect.PRONE))

    def test_grapple_state_penalties_and_movement(self):
        eng, a, d = self.duel()
        eng._begin_grapple(a, d)
        self.assertTrue(d.has_status(StatusEffect.GRAPPLED))
        self.assertEqual(d.physical_penalty(), -3)  # the grappled target
        self.assertEqual(a.physical_penalty(), -3)  # the grappler too
        # A grappled combatant cannot move or dash.
        self.assertFalse(eng.action_move(d, 2, 0))
        self.assertFalse(eng.action_dash(d, 5, 0))
        # Being knocked Prone ends the grapple for everyone involved.
        eng._set_prone(d)
        self.assertFalse(d.has_status(StatusEffect.GRAPPLED))
        self.assertEqual(a.physical_penalty(), 0)

    def test_grapple_action_crit_succeeds(self):
        eng, a, d = self.duel()
        with patch.object(engine_module, "roll_2d10", _crit):
            r = eng.action_grapple(a, d)
        self.assertTrue(r["success"])
        self.assertTrue(d.has_status(StatusEffect.GRAPPLED))
        # Grapple is a 1-action maneuver, NOT Limited.
        self.assertFalse(a.limited_action_used)

    def test_struggle_breaks_free(self):
        eng, a, d = self.duel()
        eng._begin_grapple(a, d)
        # Equal stats + equal rolls => the struggler meets/beats and escapes.
        with patch.object(engine_module, "roll_2d10", _fixed(12, 6, 6)):
            r = eng.action_struggle(d)
        self.assertTrue(r["success"])
        self.assertFalse(d.has_status(StatusEffect.GRAPPLED))

    def test_disarm_requires_grapple_and_drops_weapon(self):
        eng, a, d = self.duel()
        # Cannot disarm without grappling first.
        self.assertFalse(eng.action_disarm(a, d)["used"])
        eng._begin_grapple(a, d)
        with patch.object(engine_module, "roll_2d10", _fixed(20, 10, 9)):
            r = eng.action_disarm(a, d)
        self.assertTrue(r["used"])
        if r["success"]:
            self.assertIsNone(d.weapon_main)
            self.assertFalse(d.has_status(StatusEffect.GRAPPLED))  # disarm ends grapple

    def test_pull_requires_whip_or_meteor_hammer(self):
        eng, a, d = self.duel(weapon="Unarmed")
        self.assertFalse(eng.action_pull(a, d)["used"])


class TestCoreResolution(ActionEconomyBase):
    def test_evasion_modifier_capped_at_3(self):
        c = Character("Acrobat")
        c.base_stats["Dexterity"] = 3
        c.base_skills["Dexterity"]["Acrobatics"] = 3  # proficiency +6, capped to +3
        p = CombatParticipant(c, 20, 20)
        self.assertEqual(p.get_evasion_modifier(), 3)

    def test_critical_hit_is_armor_piercing(self):
        eng, a, d = self.duel()
        d.armor = AVALORE_ARMOR["Heavy Armor"]  # would soak a normal Unarmed hit
        hp_before = d.current_hp
        with patch.object(engine_module, "roll_2d10", _crit):
            res = eng.perform_attack(a, d, a.weapon_main)
        self.assertTrue(res["is_crit"])
        # A crit deals AP damage regardless of armour.
        self.assertEqual(hp_before - d.current_hp, AVALORE_WEAPONS["Unarmed"].damage)


class TestStealth(ActionEconomyBase):
    def _stealthy_attacker(self, a):
        # High Stealth so the defender's Perception check does not detect the sneak.
        a.character.base_stats["Dexterity"] = 3
        a.character.base_skills["Dexterity"]["Stealth"] = 3

    def test_hidden_attacker_sneak_attack_bypasses_block(self):
        eng, a, d = self.duel()
        self._stealthy_attacker(a)
        d.shield = AVALORE_SHIELDS["Large Shield"]
        d.is_blocking = True
        a.apply_status(StatusEffect.HIDDEN)
        hp_before = d.current_hp
        # A normal attack here could be blocked; a Sneak Attack cannot be.
        with patch.object(engine_module, "roll_2d10", _fixed(14, 7, 7)):
            res = eng.perform_attack(a, d, a.weapon_main)
        self.assertTrue(res["hit"])
        self.assertFalse(res["blocked"])
        self.assertLess(d.current_hp, hp_before)
        # Attacking reveals the attacker.
        self.assertFalse(a.has_status(StatusEffect.HIDDEN))

    def test_sneak_attack_bypasses_evade(self):
        eng, a, d = self.duel()
        self._stealthy_attacker(a)
        d.is_evading = True
        a.apply_status(StatusEffect.HIDDEN)
        # Without the sneak the equal evade roll would at least graze; the Sneak
        # Attack skips evasion entirely, so it lands as a clean (non-graze) hit.
        with patch.object(engine_module, "roll_2d10", _fixed(14, 7, 7)):
            res = eng.perform_attack(a, d, a.weapon_main)
        self.assertTrue(res["hit"])
        self.assertFalse(res["is_graze"])

    def test_hide_action_sets_hidden_on_success(self):
        eng, a, d = self.duel()
        a.character.base_stats["Dexterity"] = 2
        a.character.base_skills["Dexterity"]["Stealth"] = 1
        with patch.object(engine_module, "roll_2d10", _fixed(12, 6, 6)):
            r = eng.action_hide(a)
        self.assertTrue(r["success"])
        self.assertTrue(a.has_status(StatusEffect.HIDDEN))


class TestDeathBleedout(ActionEconomyBase):
    def _make_critical(self, name="V"):
        p = CombatParticipant(Character(name), 1, 20)
        p.take_damage(1)  # 1 -> 0 HP: becomes Critical (no save yet)
        self.assertTrue(p.is_critical)
        self.assertFalse(p.in_bleedout)
        return p

    def test_failed_death_save_enters_bleedout_not_death(self):
        p = self._make_critical()
        with patch("combat.dice.roll_2d10", return_value=(3, (1, 2))):
            p.take_damage(1)  # Critical + damage -> Death Save -> fails
        self.assertTrue(p.in_bleedout)
        self.assertFalse(p.is_dead)
        self.assertFalse(p.is_critical)
        self.assertGreaterEqual(p.bleedout_turns_remaining, 1)
        self.assertTrue(p.has_status(StatusEffect.BLEEDOUT))

    def test_bleedout_counts_down_to_death(self):
        p = self._make_critical()
        with patch("combat.dice.roll_2d10", return_value=(3, (1, 2))):
            p.take_damage(1)
        # HAR:Belief defaults to 0 -> 1 turn of bleedout, then death.
        self.assertEqual(p.bleedout_turns_remaining, 1)
        p.start_turn()
        self.assertTrue(p.is_dead)

    def test_crit_success_death_save_recovers(self):
        p = self._make_critical("W")
        with patch("combat.dice.roll_2d10", return_value=(20, (10, 10))):
            p.take_damage(1)  # crit success on the death save
        self.assertFalse(p.is_critical)
        self.assertFalse(p.in_bleedout)
        self.assertGreaterEqual(p.current_hp, 1)

    def test_damage_in_bleedout_kills(self):
        p = self._make_critical()
        p._enter_bleedout()
        p.take_damage(1)
        self.assertTrue(p.is_dead)

    def test_heal_lifts_bleedout(self):
        p = self._make_critical()
        p._enter_bleedout()
        p.heal(5)
        self.assertFalse(p.in_bleedout)
        self.assertFalse(p.is_critical)
        self.assertEqual(p.current_hp, 5)

    def test_exempt_actions_do_not_trigger_death_save(self):
        p = self._make_critical("X")
        for exempt in ("evade", "block", "dash", "struggle", "hide", "conceal", "load Crossbow"):
            p.last_death_save_triggered = False
            p.actions_remaining = 5
            p.consume_action(1, action_name=exempt)
            self.assertFalse(p.last_death_save_triggered, f"{exempt} should be exempt")
        # A normal attack while Critical DOES trigger a death save.
        p.last_death_save_triggered = False
        p.consume_action(1, action_name="attack with Unarmed")
        self.assertTrue(p.last_death_save_triggered)

    def test_stabilize_halts_countdown(self):
        eng, a, d = self.duel()
        d._enter_bleedout()
        a.character.base_stats["Intelligence"] = 2
        a.character.base_skills["Intelligence"]["Healing"] = 1
        a.position = (0, 0)
        d.position = (1, 0)
        with patch.object(engine_module, "roll_2d10", _fixed(12, 6, 6)):
            r = eng.action_stabilize(a, d)
        self.assertTrue(r["used"])
        self.assertTrue(r["success"])
        self.assertTrue(d.stabilized)
        # A stabilized character no longer counts down.
        turns = d.bleedout_turns_remaining
        d.start_turn()
        self.assertEqual(d.bleedout_turns_remaining, turns)
        self.assertFalse(d.is_dead)


if __name__ == "__main__":
    unittest.main()
