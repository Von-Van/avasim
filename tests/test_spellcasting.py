"""
Canonical spellcasting tests (avalore.net/arcane + Grimoire).

Covers the casting procedure (cantrips, DC 10, crit casts, primary
discipline, miscasts, the overcast 1d6 table) and the mechanical behaviour
of engine-wired Grimoire spells.
"""

import unittest
from unittest.mock import patch

import combat.engine as engine_module
from combat import (
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
    AVALORE_WEAPONS,
    AVALORE_SPELLS,
    StatusEffect,
)
from combat.spells import MAGE_LEVELS, OPPOSED_DISCIPLINES
from avasim import Character


def _fixed(total, d1, d2):
    return lambda: (total, (d1, d2))


def spell(name):
    return AVALORE_SPELLS[name]


class CastingBase(unittest.TestCase):
    def duel(self, gap=1, anima=14, arcana=2, primary=""):
        caster_char = Character("Mage")
        caster_char.base_skills["Harmony"]["Arcana"] = arcana
        caster = CombatParticipant(caster_char, 20, 20, anima=anima, max_anima=anima,
                                   weapon_main=AVALORE_WEAPONS["Unarmed"])
        caster.primary_discipline = primary
        target = CombatParticipant(Character("Target"), 20, 20,
                                   weapon_main=AVALORE_WEAPONS["Unarmed"])
        caster.team, target.team = "A", "B"
        tmap = TacticalMap(40, 40)
        caster.position = (0, 0)
        target.position = (gap, 0)
        tmap.set_occupant(*caster.position, caster)
        tmap.set_occupant(*target.position, target)
        eng = AvaCombatEngine([caster, target], tmap)
        caster.actions_remaining = 5
        target.actions_remaining = 5
        return eng, caster, target


class TestCastingProcedure(CastingBase):
    def test_cantrip_auto_succeeds_without_roll_or_anima(self):
        eng, caster, target = self.duel(anima=0)
        res = eng.perform_cast_spell(caster, spell("Whisper"), None)
        self.assertTrue(res["success"])
        self.assertTrue(res["cantrip"])
        self.assertEqual(caster.anima, 0)

    def test_dc_10_success_consumes_anima(self):
        eng, caster, target = self.duel(gap=4, arcana=0)
        with patch.object(engine_module, "roll_2d10", _fixed(10, 5, 5)):
            res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertTrue(res["success"])
        self.assertEqual(caster.anima, 14 - 4)

    def test_miscast_below_10_loses_half_anima(self):
        eng, caster, target = self.duel(gap=4, arcana=0)
        with patch.object(engine_module, "roll_2d10", _fixed(9, 4, 5)):
            res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertTrue(res["miscast"])
        self.assertEqual(caster.anima, 14 - 2)  # half of 4

    def test_primary_discipline_miscast_costs_nothing_and_casts_at_plus_one(self):
        eng, caster, target = self.duel(gap=4, arcana=0, primary="Ichor")
        # Roll of 9 + 1 (primary) = 10 -> succeeds where a non-primary fails.
        with patch.object(engine_module, "roll_2d10", _fixed(9, 4, 5)):
            res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertTrue(res["success"])
        # Roll of 8 + 1 = 9 -> miscast, but a primary miscast consumes no anima.
        caster.anima = 14
        with patch.object(engine_module, "roll_2d10", _fixed(8, 4, 4)):
            res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertTrue(res["miscast"])
        self.assertEqual(caster.anima, 14)

    def test_critical_cast_consumes_no_anima(self):
        eng, caster, target = self.duel(gap=4, arcana=0)
        with patch.object(engine_module, "roll_2d10", _fixed(20, 10, 10)):
            res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertTrue(res["success"])
        self.assertTrue(res["crit"])
        self.assertEqual(caster.anima, 14)

    def test_overcast_miscast_knocks_unconscious(self):
        eng, caster, target = self.duel(gap=4, anima=1, arcana=0)
        caster.max_anima = 14
        with patch.object(engine_module, "roll_2d10", _fixed(9, 4, 5)):
            res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertTrue(res["miscast"])
        self.assertTrue(res["overcast"])
        self.assertEqual(caster.current_hp, 0)
        self.assertEqual(caster.anima, 0)
        self.assertTrue(caster.has_overcast_today)

    def test_overcast_once_per_day(self):
        eng, caster, target = self.duel(gap=4, anima=0, arcana=0)
        caster.max_anima = 14
        caster.has_overcast_today = True
        res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertFalse(res["success"])

    def test_overcast_consequence_weakness_applies_str_penalty(self):
        eng, caster, target = self.duel(gap=4, anima=0, arcana=3)
        caster.max_anima = 14
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)), \
             patch.object(engine_module, "roll_1d6", lambda: 4):
            res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertTrue(res["success"])
        self.assertTrue(res["overcast"])
        self.assertEqual(caster.check_penalty("Strength", "Athletics"), -1)
        self.assertEqual(caster.check_penalty("Strength"), -1)

    def test_spell_range_band_enforced(self):
        eng, caster, target = self.duel(gap=12)  # beyond skirmishing reach (8)
        res = eng.perform_cast_spell(caster, spell("Syphon"), target)
        self.assertFalse(res["success"])
        self.assertEqual(caster.anima, 14)

    def test_action_cast_spell_consumes_listed_actions(self):
        eng, caster, target = self.duel(gap=4)
        caster.actions_remaining = 2
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.action_cast_spell(caster, spell("Staunch"), target)  # 2 actions
        self.assertTrue(res["success"])
        self.assertEqual(caster.actions_remaining, 0)

    def test_rituals_cannot_be_cast_in_combat(self):
        eng, caster, target = self.duel()
        res = eng.action_cast_spell(caster, spell("Graveblossom"), target)  # 10 actions
        self.assertFalse(res["success"])

    def test_unwired_spell_resolves_without_combat_effect(self):
        eng, caster, target = self.duel(gap=4)
        hp = target.current_hp
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.perform_cast_spell(caster, spell("Tongue Tie"), target)
        self.assertTrue(res["success"])
        self.assertEqual(target.current_hp, hp)


class TestWiredSpells(CastingBase):
    def cast(self, eng, caster, target, name, cast_roll=(18, 9, 9), save_roll=None):
        rolls = [cast_roll]
        if save_roll:
            rolls.append(save_roll)
        seq = iter(rolls)

        def fake_roll():
            try:
                total, d1, d2 = next(seq)
            except StopIteration:
                total, d1, d2 = 5, 2, 3
            return total, (d1, d2)

        with patch.object(engine_module, "roll_2d10", fake_roll):
            return eng.perform_cast_spell(caster, spell(name), target)

    def test_syphon_damage_on_failed_save(self):
        eng, caster, target = self.duel(gap=4)
        res = self.cast(eng, caster, target, "Syphon", save_roll=(5, 2, 3))
        self.assertEqual(res["damage"], 4)  # AP: ignores armor
        self.assertEqual(target.current_hp, 16)

    def test_syphon_negated_on_save(self):
        eng, caster, target = self.duel(gap=4)
        res = self.cast(eng, caster, target, "Syphon", save_roll=(15, 7, 8))
        self.assertEqual(res["damage"], 0)
        self.assertEqual(target.current_hp, 20)

    def test_crawling_hex_half_damage_on_save(self):
        eng, caster, target = self.duel(gap=4)
        res = self.cast(eng, caster, target, "Crawling Hex", save_roll=(15, 7, 8))
        self.assertEqual(res["damage"], 2)

    def test_detain_slows_on_failed_save(self):
        eng, caster, target = self.duel(gap=4)
        self.cast(eng, caster, target, "Detain", save_roll=(5, 2, 3))
        self.assertTrue(target.has_status(StatusEffect.SLOWED))

    def test_seize_immobilizes_and_blocks_movement(self):
        eng, caster, target = self.duel(gap=1)
        self.cast(eng, caster, target, "Seize", save_roll=(5, 2, 3))
        self.assertTrue(target.has_status(StatusEffect.IMMOBILIZED))
        moved = eng.action_move(target, 5, 5)
        self.assertFalse(moved)

    def test_weep_dot_ticks_at_turn_start(self):
        eng, caster, target = self.duel(gap=4)
        self.cast(eng, caster, target, "Weep", save_roll=(5, 2, 3))
        self.assertEqual(len(target.active_dots), 1)
        target.start_turn()
        self.assertEqual(target.current_hp, 18)
        target.start_turn()
        target.start_turn()
        self.assertEqual(target.current_hp, 14)
        self.assertEqual(target.active_dots, [])
        target.start_turn()
        self.assertEqual(target.current_hp, 14)

    def test_atmokinesis_burning_escalates(self):
        eng, caster, target = self.duel(gap=4)
        res = self.cast(eng, caster, target, "Atmokinesis")
        self.assertEqual(res["damage"], 3)
        target.start_turn()  # 4 fire
        target.start_turn()  # 5 fire
        self.assertEqual(target.current_hp, 20 - 3 - 4 - 5)

    def test_triage_heals_dice_plus_arcana_and_stabilizes(self):
        eng, caster, ally = self.duel(gap=1, arcana=2)
        ally.team = "A"  # make them an ally
        ally.current_hp = 0
        ally.is_critical = True
        ally._enter_bleedout()
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)), \
             patch.object(engine_module.current_rng(), "randint", lambda a, b: 3):
            res = eng.perform_cast_spell(caster, spell("Triage"), ally)
        self.assertEqual(res["healing"], 5)  # 3 (1d4 forced) + 2 arcana
        self.assertEqual(ally.current_hp, 5)
        self.assertFalse(ally.in_bleedout)  # healing lifts bleedout

    def test_staunch_stabilizes_bleedout(self):
        eng, caster, ally = self.duel(gap=4)
        ally.team = "A"
        ally.current_hp = 0
        ally._enter_bleedout()
        countdown = ally.bleedout_turns_remaining
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            eng.perform_cast_spell(caster, spell("Staunch"), ally)
        self.assertTrue(ally.stabilized)
        ally.start_turn()
        self.assertEqual(ally.bleedout_turns_remaining, countdown)

    def test_transfuse_costs_caster_hp(self):
        eng, caster, ally = self.duel(gap=1, arcana=3)
        ally.team = "A"
        ally.current_hp = 10
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.perform_cast_spell(caster, spell("Transfuse"), ally)
        self.assertEqual(res["healing"], 7)  # 4 + arcana capped at 3
        self.assertEqual(ally.current_hp, 17)
        self.assertEqual(caster.current_hp, 13)

    def test_corrupt_blocks_healing(self):
        eng, caster, target = self.duel(gap=4)
        target.current_hp = 10
        self.cast(eng, caster, target, "Corrupt", save_roll=(5, 2, 3))
        self.assertTrue(target.has_status(StatusEffect.CORRUPTED))
        hp_after_hex = target.current_hp
        target.heal(5)
        self.assertEqual(target.current_hp, hp_after_hex)

    def test_fortify_grants_ap_immunity(self):
        eng, caster, ally = self.duel(gap=1)
        ally.team = "A"
        caster.character.base_skills["Strength"]["Forging"] = 2
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            eng.perform_cast_spell(caster, spell("Fortify"), ally)
        self.assertEqual(ally.ap_ward_rounds, 2)
        from combat import AVALORE_ARMOR
        ally.armor = AVALORE_ARMOR["Heavy Armor"]
        ally.character.base_skills["Strength"]["Athletics"] = 3  # meet heavy reqs
        hp = ally.current_hp
        ally.take_damage(3, armor_piercing=True)
        taken = hp - ally.current_hp
        self.assertLess(taken, 3)  # heavy armor soaks 1d3 despite the AP hit

    def test_acceleration_grants_extra_action_and_move(self):
        eng, caster, ally = self.duel(gap=4)
        ally.team = "A"
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            eng.perform_cast_spell(caster, spell("Acceleration"), ally)
        ally.start_turn()
        self.assertEqual(ally.actions_remaining, 3)
        self.assertEqual(ally.bonus_move_this_turn, 3)
        ally.start_turn()
        self.assertEqual(ally.actions_remaining, 2)

    def test_buffer_turns_hit_into_graze(self):
        eng, caster, target = self.duel(gap=1)
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            eng.perform_cast_spell(caster, spell("Buffer"), caster)
        self.assertEqual(caster.buffer_charges, 1)
        target.actions_remaining = 2
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)), \
             patch.object(engine_module, "roll_1d2", lambda: 2):
            res = eng.perform_attack(target, caster, target.weapon_main)
        self.assertTrue(res["hit"])
        self.assertEqual(res["damage"], 1)  # unarmed 2 halved
        self.assertEqual(caster.buffer_charges, 0)

    def test_barbs_retaliate_against_melee(self):
        eng, caster, target = self.duel(gap=1)
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            eng.perform_cast_spell(caster, spell("Barbs"), None)
        self.assertEqual(caster.barbs_charges, 3)
        target.actions_remaining = 2
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            eng.perform_attack(target, caster, target.weapon_main)
        self.assertEqual(target.current_hp, 19)
        self.assertEqual(caster.barbs_charges, 2)

    def test_kinetic_spike_boosts_next_attack_with_knockback(self):
        eng, caster, target = self.duel(gap=1)
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            eng.perform_cast_spell(caster, spell("Kinetic Spike"), caster)
        self.assertTrue(caster.kinetic_spike_ready)
        caster.actions_remaining = 2
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.perform_attack(caster, target, caster.weapon_main)
        self.assertTrue(res["hit"])
        self.assertEqual(res["damage"], 3)  # unarmed 1 + 2 spike
        self.assertFalse(caster.kinetic_spike_ready)
        self.assertGreater(eng.get_distance(caster, target), 1)  # hurled away

    def test_eidetic_echo_decoys_absorb_attacks(self):
        eng, caster, target = self.duel(gap=1, arcana=3)
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            eng.perform_cast_spell(caster, spell("Eidetic Echo"), None)
        self.assertEqual(caster.duplicate_images, 3)
        target.actions_remaining = 4

        class _PickDecoy:
            def randint(self, a, b):
                return b  # always strike a duplicate

        with patch.object(engine_module, "current_rng", lambda: _PickDecoy()):
            res = eng.perform_attack(target, caster, target.weapon_main)
        self.assertFalse(res["hit"])
        self.assertEqual(caster.duplicate_images, 2)
        self.assertEqual(caster.current_hp, 20)

    def test_pierce_penumbra_caps_targets_by_arcana(self):
        eng, caster, target = self.duel(gap=4, arcana=0)
        # Only the one hostile target in radius; unavoidable 2 AP.
        with patch.object(engine_module, "roll_2d10", _fixed(15, 7, 8)):
            res = eng.perform_cast_spell(caster, spell("Pierce Penumbra"), target)
        self.assertEqual(res["damage"], 2)

    def test_kinetic_array_can_be_evaded_against_cast_roll(self):
        eng, caster, target = self.duel(gap=4, arcana=0)
        target.is_evading = True
        target.character.base_skills["Dexterity"]["Acrobatics"] = 3
        # Cast total 12; evasion roll 10 + 3 = 13 >= 12 evades.
        rolls = iter([(12, (6, 6)), (10, (5, 5))])
        with patch.object(engine_module, "roll_2d10", lambda: next(rolls)):
            res = eng.perform_cast_spell(caster, spell("Kinetic Array"), target)
        self.assertEqual(res["damage"], 0)
        self.assertEqual(target.current_hp, 20)

    def test_sabotage_disarms_weapon(self):
        eng, caster, target = self.duel(gap=4)
        target.weapon_main = AVALORE_WEAPONS["Arming Sword"]
        self.cast(eng, caster, target, "Sabotage", save_roll=(5, 2, 3))
        self.assertTrue(target.has_status(StatusEffect.DISARMED))
        target.actions_remaining = 2
        res = eng.perform_attack(target, caster, target.weapon_main)
        self.assertFalse(res["hit"])


class TestAICasting(CastingBase):
    def test_ai_casts_when_spell_beats_weapon(self):
        from combat.ai import CombatAI
        eng, caster, target = self.duel(gap=4, arcana=3)
        caster.known_spells = ["Syphon", "Whisper"]  # Whisper is unwired and ignored
        ai = CombatAI(strategy="balanced", show_decisions=True)
        ai.decide_turn(eng, caster)
        self.assertTrue(any("casts Syphon" in line for line in eng.combat_log),
                        "AI should cast Syphon when its EV beats an unarmed swing")

    def test_ai_stabilizes_downed_ally_first(self):
        from combat.ai import CombatAI
        eng, caster, target = self.duel(gap=4, arcana=3)
        ally = CombatParticipant(Character("Ally"), 20, 20,
                                 weapon_main=AVALORE_WEAPONS["Unarmed"])
        ally.team = "A"
        ally.position = (0, 1)
        eng.tactical_map.set_occupant(0, 1, ally)
        eng.participants.append(ally)
        ally.current_hp = 0
        ally._enter_bleedout()
        caster.known_spells = ["Staunch"]
        ai = CombatAI(strategy="balanced", show_decisions=True)
        ai.decide_turn(eng, caster)
        self.assertTrue(any("casts Staunch" in line for line in eng.combat_log),
                        "AI should prioritize stabilizing the bleeding-out ally")


class TestArcaneConstants(unittest.TestCase):
    def test_mage_levels_match_canon(self):
        self.assertEqual(MAGE_LEVELS[1], (8, 6))
        self.assertEqual(MAGE_LEVELS[2], (14, 10))
        self.assertEqual(MAGE_LEVELS[3], (20, 14))
        self.assertEqual(MAGE_LEVELS[4], (30, 20))

    def test_magic_wheel_opposition_is_symmetric(self):
        self.assertEqual(OPPOSED_DISCIPLINES["Tellurgy"], "Ether")
        self.assertEqual(OPPOSED_DISCIPLINES["Ichor"], "Artifice")
        self.assertEqual(OPPOSED_DISCIPLINES["Cursesmithy"], "Force")
        for a, b in OPPOSED_DISCIPLINES.items():
            self.assertEqual(OPPOSED_DISCIPLINES[b], a)


if __name__ == "__main__":
    unittest.main()
