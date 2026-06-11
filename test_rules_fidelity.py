"""
Tests for the formerly-documented simplifications, now implemented to canon:

1. Multi-grappler aim bonus (+1 per grappler on melee attacks vs Grappled).
2. Bleedout half-movement crawl (no actions, but movement at half).
3. Rage stat shifts (STR/DEX +1, INT/HAR -1), 1 self-damage per turn, and
   ending on Critical.
4. LW: Skewer -1 damage per additional target.
5. Improvised weapons (-1 aim / -1 damage) and shields (-1 block), with no
   feat synergy except Rage.
"""

import unittest
from unittest.mock import patch

import combat.engine as engine_module
from combat import (
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
    AVALORE_WEAPONS,
    AVALORE_FEATS,
    StatusEffect,
)
from combat.items import make_improvised_weapon, make_improvised_shield, AVALORE_SHIELDS
from combat.validation import validate_build
from combat.contracts import CharacterBuild
from avasim import Character


def _fixed(total, d1, d2):
    return lambda: (total, (d1, d2))


def feats(*names):
    return [AVALORE_FEATS[n] for n in names]


class FidelityBase(unittest.TestCase):
    def duel(self, a_feats=(), a_weapon="Unarmed", d_weapon="Unarmed", gap=1):
        a = CombatParticipant(Character("A"), 20, 20,
                              weapon_main=AVALORE_WEAPONS[a_weapon], feats=list(feats(*a_feats)))
        d = CombatParticipant(Character("D"), 20, 20,
                              weapon_main=AVALORE_WEAPONS[d_weapon])
        a.team, d.team = "A", "B"
        tmap = TacticalMap(20, 20)
        a.position = (0, 0)
        d.position = (gap, 0)
        tmap.set_occupant(*a.position, a)
        tmap.set_occupant(*d.position, d)
        eng = AvaCombatEngine([a, d], tmap)
        a.actions_remaining = 5
        d.actions_remaining = 5
        return eng, a, d


class TestMultiGrapplerBonus(FidelityBase):
    def test_melee_attacks_gain_plus_one_per_grappler(self):
        eng, a, d = self.duel()
        # Two grapplers hold the defender.
        g2 = CombatParticipant(Character("G2"), 20, 20, weapon_main=AVALORE_WEAPONS["Unarmed"])
        g2.team = "A"
        g2.position = (1, 1)
        eng.tactical_map.set_occupant(1, 1, g2)
        eng.participants.append(g2)
        eng._begin_grapple(a, d)
        eng._begin_grapple(g2, d)
        # Unarmed +2; roll 8; grappled attacker penalty does not apply to A
        # (A is the grappler, -3 physical applies to both sides per canon).
        with patch.object(engine_module, "roll_2d10", _fixed(8, 4, 4)):
            res = eng.perform_attack(a, d, a.weapon_main)
        # 8 + 2 (unarmed) - 3 (grappling penalty) + 2 (two grapplers) = 9 < 12 miss;
        # without the bonus it would be 7. Verify via the log line instead.
        self.assertTrue(any("+2 aim (2 grappler(s)" in line for line in eng.combat_log))

    def test_ranged_attacks_get_no_grappler_bonus(self):
        eng, a, d = self.duel(a_weapon="Longbow", gap=8)
        g2 = CombatParticipant(Character("G2"), 20, 20, weapon_main=AVALORE_WEAPONS["Unarmed"])
        g2.team = "A"
        g2.position = (7, 0)
        eng.tactical_map.set_occupant(7, 0, g2)
        eng.participants.append(g2)
        eng._begin_grapple(g2, d)
        a.drawn_weapon = "Longbow"
        with patch.object(engine_module, "roll_2d10", _fixed(8, 4, 4)):
            eng.perform_attack(a, d, a.weapon_main)
        self.assertFalse(any("grappler(s) holding them" in line for line in eng.combat_log))


class TestBleedoutCrawl(FidelityBase):
    def test_bleeding_out_combatant_crawls_at_half_movement(self):
        eng, a, d = self.duel()
        a.character.base_skills["Harmony"]["Belief"] = 3  # 3-turn countdown
        a.current_hp = 0
        a._enter_bleedout()
        a.start_turn()
        self.assertEqual(a.actions_remaining, 0)
        # Half of base 5, rounded up = 3 blocks: (0,0) -> (0,3) is allowed.
        self.assertTrue(eng.action_move(a, 0, 3))
        self.assertEqual(a.position, (0, 3))

    def test_crawl_cannot_exceed_half_movement(self):
        eng, a, d = self.duel()
        a.current_hp = 0
        a._enter_bleedout()
        a.start_turn()
        self.assertFalse(eng.action_move(a, 0, 5))  # 5 > half allowance

    def test_dash_remains_impossible_while_bleeding_out(self):
        eng, a, d = self.duel()
        a.current_hp = 0
        a._enter_bleedout()
        a.start_turn()
        self.assertFalse(eng.action_dash(a, 0, 4))


class TestRageCanon(FidelityBase):
    def test_rage_shifts_stats_and_burns_each_turn(self):
        eng, a, d = self.duel(a_feats=("Rage",))
        base_str = a.character.base_stats["Strength"]
        base_int = a.character.base_stats["Intelligence"]
        res = eng.action_rage(a)
        self.assertTrue(res["used"])
        self.assertEqual(a.character.base_stats["Strength"], base_str + 1)
        self.assertEqual(a.character.base_stats["Intelligence"], base_int - 1)
        hp = a.current_hp
        a.start_turn()
        self.assertEqual(a.current_hp, hp - 1)  # the Rage burns its host

    def test_rage_ends_on_critical_and_reverts_stats(self):
        eng, a, d = self.duel(a_feats=("Rage",))
        base_stats = dict(a.character.base_stats)
        eng.action_rage(a)
        a.take_damage(a.current_hp, armor_piercing=True)  # drop to 0 -> Critical
        self.assertTrue(a.is_critical)
        self.assertFalse(a.rage_active)
        self.assertEqual(a.character.base_stats, base_stats)

    def test_rage_adjacent_foes_knocked_prone(self):
        eng, a, d = self.duel(a_feats=("Rage",))
        eng.action_rage(a)
        self.assertTrue(d.has_status(StatusEffect.PRONE))


class TestSkewerFalloff(FidelityBase):
    def test_two_targets_take_one_less_damage(self):
        eng, a, d = self.duel(a_feats=("LW: Skewer",), a_weapon="Arming Sword")
        d2 = CombatParticipant(Character("D2"), 20, 20, weapon_main=AVALORE_WEAPONS["Unarmed"])
        d2.team = "B"
        d2.position = (2, 0)
        eng.tactical_map.set_occupant(2, 0, d2)
        eng.participants.append(d2)
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.action_lw_skewer(a, 1, 0)
        self.assertTrue(res["used"])
        self.assertEqual(res["targets"], 2)
        # Arming Sword 4 damage - 1 falloff = 3 to each (no armor).
        self.assertEqual(d.current_hp, 17)
        self.assertEqual(d2.current_hp, 17)

    def test_single_target_takes_full_damage(self):
        eng, a, d = self.duel(a_feats=("LW: Skewer",), a_weapon="Arming Sword")
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.action_lw_skewer(a, 1, 0)
        self.assertEqual(res["targets"], 1)
        self.assertEqual(d.current_hp, 16)  # full 4


class TestImprovisedEquipment(FidelityBase):
    def test_improvised_weapon_penalties(self):
        sword = AVALORE_WEAPONS["Arming Sword"]
        imp = make_improvised_weapon(sword)
        self.assertEqual(imp.accuracy_bonus, sword.accuracy_bonus - 1)
        self.assertEqual(imp.damage, sword.damage - 1)
        self.assertTrue(imp.improvised)

    def test_ranged_templates_cannot_be_improvised(self):
        with self.assertRaises(ValueError):
            make_improvised_weapon(AVALORE_WEAPONS["Longbow"])

    def test_improvised_shield_blocks_at_minus_one(self):
        shield = AVALORE_SHIELDS["Small Shield"]
        imp = make_improvised_shield(shield)
        self.assertEqual(imp.block_modifier, shield.block_modifier - 1)
        self.assertTrue(imp.improvised)

    def test_improvised_weapon_skips_feat_synergy_but_keeps_rage(self):
        eng, a, d = self.duel(a_feats=("Rage",))
        a.weapon_main = make_improvised_weapon(AVALORE_WEAPONS["Arming Sword"])
        a.rage_active = True  # raging (without stat shift bookkeeping for this check)
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.perform_attack(a, d, a.weapon_main)
        self.assertTrue(res["hit"])
        # Improvised sword 3 + 1 (Rage) = 4
        self.assertEqual(res["damage"], 4)

    def test_build_factory_resolves_improvised_names(self):
        from combat.factory import build_to_participant
        build = CharacterBuild(name="Scrapper", hand1="Improvised Arming Sword", armor="None")
        p = build_to_participant(build)
        self.assertTrue(p.weapon_main.improvised)
        self.assertEqual(p.weapon_main.damage, AVALORE_WEAPONS["Arming Sword"].damage - 1)

    def test_validation_flags_improvised_ranged(self):
        build = CharacterBuild(name="Sniper", hand1="Improvised Longbow", armor="None")
        issues = validate_build(build)
        self.assertTrue(any(issue.code == "improvised_ranged" for issue in issues))

    def test_validation_accepts_improvised_melee(self):
        build = CharacterBuild(name="Scrapper", hand1="Improvised Mace", armor="None")
        issues = validate_build(build)
        self.assertFalse(any(issue.code == "unknown_equipment" for issue in issues))


if __name__ == "__main__":
    unittest.main()
