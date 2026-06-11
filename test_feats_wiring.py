"""
Focused tests for the combat feats wired into the engine in this change set
(Mutation / Vampiric / Combat / Lineage Weapon). Each test exercises one feat's
mechanical effect; out-of-combat feats (Utility/Background and narrative
Vampiric/Mutant feats) are catalog-only and covered by test_catalogs.
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
    AVALORE_FEATS,
    StatusEffect,
)
from avasim import Character


def _fixed(total, d1, d2):
    return lambda: (total, (d1, d2))


def feats(*names):
    return [AVALORE_FEATS[n] for n in names]


class WiringBase(unittest.TestCase):
    def duel(self, a_feats=(), d_feats=(), a_weapon="Unarmed", d_weapon="Unarmed",
             gap=1, size=20):
        a = CombatParticipant(Character("A"), 20, 20,
                              weapon_main=AVALORE_WEAPONS[a_weapon], feats=list(a_feats))
        d = CombatParticipant(Character("D"), 20, 20,
                              weapon_main=AVALORE_WEAPONS[d_weapon], feats=list(d_feats))
        a.team, d.team = "A", "B"
        tmap = TacticalMap(size, size)
        a.position = (0, 0)
        d.position = (gap, 0)
        tmap.set_occupant(*a.position, a)
        tmap.set_occupant(*d.position, d)
        eng = AvaCombatEngine([a, d], tmap)
        a.actions_remaining = 5
        d.actions_remaining = 5
        return eng, a, d


class TestWiredFeats(WiringBase):
    def test_martial_discipline_block_buffs_arming_sword(self):
        eng, a, d = self.duel(a_feats=feats("Martial Discipline"), a_weapon="Arming Sword")
        a.shield = AVALORE_SHIELDS["Small Shield"]
        eng.feat_registry.dispatch_on_block_success(eng, a, d)
        self.assertEqual(a.martial_discipline_next, 1)
        a.start_turn()  # stacks roll over into effect
        self.assertEqual(a.martial_discipline_stacks, 1)
        total = eng.feat_registry.dispatch_modify_attack_roll(
            eng, a, d, AVALORE_WEAPONS["Arming Sword"], 10, {})
        self.assertEqual(total, 11)

    def test_razor_claws_ignores_quickfooted(self):
        # Defender Quickfooted + evading would dodge a normal Unarmed swing;
        # Razor Claws ignores Quickfooted so the strike connects.
        eng, a, d = self.duel(d_feats=feats("Quickfooted"))
        d.character.base_skills["Dexterity"]["Acrobatics"] = 0
        d.is_evading = True
        with patch.object(engine_module, "roll_2d10", _fixed(11, 5, 6)):
            without = eng.perform_attack(a, d, AVALORE_WEAPONS["Unarmed"])
        self.assertFalse(without["hit"])  # Quickfooted carried the evade

        eng, a, d = self.duel(a_feats=feats("Razor Claws"), d_feats=feats("Quickfooted"))
        d.character.base_skills["Dexterity"]["Acrobatics"] = 0
        d.is_evading = True
        with patch.object(engine_module, "roll_2d10", _fixed(11, 5, 6)):
            with_claws = eng.perform_attack(a, d, AVALORE_WEAPONS["Unarmed"])
        self.assertTrue(with_claws["hit"])

    def test_vampiric_speed_evasion_bonus(self):
        eng, a, d = self.duel(d_feats=feats("Vampiric Speed"))
        bonus = eng.feat_registry.dispatch_modify_evasion(eng, d, AVALORE_WEAPONS["Unarmed"], 0, {})
        self.assertEqual(bonus, 1)

    def test_ambush_predator_first_round_bonus(self):
        eng, a, d = self.duel(a_feats=feats("Ambush Predator"))
        eng.round = 1
        d.has_taken_turn = False
        self.assertEqual(eng.feat_registry.dispatch_modify_attack_roll(eng, a, d, AVALORE_WEAPONS["Unarmed"], 10, {}), 11)
        d.has_taken_turn = True
        self.assertEqual(eng.feat_registry.dispatch_modify_attack_roll(eng, a, d, AVALORE_WEAPONS["Unarmed"], 10, {}), 10)

    def test_wounded_animal_self_stabilizes_in_bleedout(self):
        eng, a, d = self.duel(a_feats=feats("Wounded Animal"))
        a._enter_bleedout()
        a.start_turn()  # on_turn_start hook fires before the countdown
        self.assertTrue(a.stabilized)
        self.assertFalse(a.is_dead)

    def test_rage_grants_damage_and_prones_adjacent(self):
        eng, a, d = self.duel(a_feats=feats("Rage"))
        res = eng.action_rage(a)
        self.assertTrue(res["used"])
        self.assertTrue(a.rage_active)
        self.assertTrue(d.has_status(StatusEffect.PRONE))
        dmg = eng.feat_registry.dispatch_modify_damage(eng, a, d, AVALORE_WEAPONS["Unarmed"], 3, {})
        self.assertEqual(dmg, 4)

    def test_acidic_blood_reflects_to_melee_attacker(self):
        eng, a, d = self.duel(d_feats=feats("Acidic Blood"))
        a_hp = a.current_hp
        with patch.object(engine_module, "roll_2d10", _fixed(16, 8, 8)):
            res = eng.perform_attack(a, d, AVALORE_WEAPONS["Unarmed"])
        self.assertTrue(res["hit"])
        self.assertEqual(a.current_hp, a_hp - 1)  # 1 reflected

    def test_unyielding_reflex_intercepts_ranged(self):
        eng, a, d = self.duel(a_weapon="Recurve Bow", d_feats=feats("Unyielding Reflex"), gap=6)
        a.character.base_stats["Dexterity"] = 2  # meet the bow's requirement
        a.character.base_skills["Dexterity"]["Finesse"] = 2
        d.character.base_stats["Dexterity"] = 3
        d.character.base_skills["Dexterity"]["Finesse"] = 3  # +3, -2 = +1 -> needs 11+
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.perform_attack(a, d, AVALORE_WEAPONS["Recurve Bow"])
        self.assertFalse(res["hit"])
        self.assertTrue(d.unyielding_reflex_used_round)

    def test_lw_skewer_is_limited_and_hits_line(self):
        eng, a, d = self.duel(a_feats=feats("Lineage Weapon", "LW: Skewer"), a_weapon="Arming Sword", gap=2)
        with patch.object(engine_module, "roll_2d10", _fixed(16, 8, 8)):
            res = eng.action_lw_skewer(a, d.position[0], d.position[1])
        self.assertTrue(res["used"])
        self.assertGreaterEqual(res["targets"], 1)
        self.assertTrue(a.limited_action_used)

    def test_pounce_leaps_and_strikes_and_is_limited(self):
        eng, a, d = self.duel(a_feats=feats("Pounce"), gap=3)
        with patch.object(engine_module, "roll_2d10", _fixed(16, 8, 8)):
            res = eng.action_pounce(a, d.position[0] - 1, d.position[1], target=d)
        self.assertTrue(res["used"])
        self.assertTrue(a.limited_action_used)
        self.assertEqual(a.position, (d.position[0] - 1, d.position[1]))


if __name__ == "__main__":
    unittest.main()
