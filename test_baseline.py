"""
Baseline regression tests for AvaSim combat engine.

These tests lock down the current Python engine behavior using deterministic
fixtures. They MUST pass before any architectural changes (Rust port, etc.).

Each test:
1. Loads a fixture scenario (input + expected output)
2. Sets the RNG seed for deterministic behavior
3. Runs the scenario
4. Asserts exact match with expected outputs

If these tests fail after changes, behavior has drifted from baseline.
"""

import unittest
import json
from pathlib import Path
from typing import Dict, Any

from combat import (
    AvaCombatEngine, CombatParticipant, TacticalMap, TerrainType,
    AVALORE_WEAPONS, AVALORE_ARMOR, AVALORE_SHIELDS, AVALORE_FEATS,
    StatusEffect, set_seed
)
from avasim import Character


class BaselineRegressionTests(unittest.TestCase):
    """Regression tests using deterministic fixtures."""

    @classmethod
    def setUpClass(cls):
        """Load all fixture files once."""
        cls.fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
        cls.fixtures = {}

        for fixture_file in sorted(cls.fixtures_dir.glob("*.json")):
            with open(fixture_file, 'r') as f:
                fixture = json.load(f)
                cls.fixtures[fixture["name"]] = fixture

    def _run_fixture(self, fixture_name: str, scenario_func):
        """Helper to run a fixture scenario and validate output."""
        fixture = self.fixtures[fixture_name]
        seed = fixture["seed"]
        expected = fixture["expected_output"]

        set_seed(seed)
        actual = scenario_func()

        # Assert each expected output field matches
        for key, expected_value in expected.items():
            self.assertEqual(
                actual[key], expected_value,
                f"Fixture {fixture_name}: {key} mismatch. Expected {expected_value}, got {actual[key]}"
            )

    def test_01_basic_melee(self):
        """Baseline: Basic melee attack sequence."""
        def scenario():
            warrior = Character("Warrior")
            warrior.base_stats["Strength"] = 3
            warrior.base_skills["Strength"]["Athletics"] = 2

            p1 = CombatParticipant(warrior, 20, 20, weapon_main=AVALORE_WEAPONS["Arming Sword"])
            p2 = CombatParticipant(Character("Target"), 20, 20)

            tmap = TacticalMap(10, 10)
            p1.position = (5, 5)
            p2.position = (6, 5)
            tmap.set_occupant(*p1.position, p1)
            tmap.set_occupant(*p2.position, p2)

            p1.actions_remaining = 10
            engine = AvaCombatEngine([p1, p2], tmap)

            for _ in range(3):
                engine.perform_attack(p1, p2, p1.weapon_main)

            return {
                "defender_hp": p2.current_hp,
                "defender_max_hp": p2.max_hp,
                "attacker_actions_used": 10 - p1.actions_remaining
            }

        self._run_fixture("01_basic_melee", scenario)

    def test_02_ranged_los(self):
        """Baseline: Ranged combat with line of sight."""
        def scenario():
            archer = Character("Archer")
            archer.base_stats["Dexterity"] = 2
            archer.base_skills["Dexterity"]["Acrobatics"] = 1
            archer.base_stats["Strength"] = 2
            archer.base_skills["Strength"]["Athletics"] = 1

            p1 = CombatParticipant(archer, 20, 20, weapon_main=AVALORE_WEAPONS["Longbow"])
            p2 = CombatParticipant(Character("Target"), 20, 20)

            tmap = TacticalMap(20, 20)
            p1.position = (0, 5)
            p2.position = (15, 5)
            tmap.set_occupant(*p1.position, p1)
            tmap.set_occupant(*p2.position, p2)

            p1.actions_remaining = 10
            engine = AvaCombatEngine([p1, p2], tmap)

            engine.perform_attack(p1, p2, p1.weapon_main)
            engine.perform_attack(p1, p2, p1.weapon_main)

            return {
                "defender_hp": p2.current_hp,
                "attacker_actions_remaining": p1.actions_remaining
            }

        self._run_fixture("02_ranged_los", scenario)

    def test_03_movement_oa(self):
        """Baseline: Movement triggering opportunity attack."""
        def scenario():
            defender = Character("Defender")
            defender.base_stats["Strength"] = 3
            defender.base_skills["Strength"]["Athletics"] = 2

            p1 = CombatParticipant(
                defender, 20, 20,
                weapon_main=AVALORE_WEAPONS["Polearm"],
                feats=[AVALORE_FEATS["Steadfast Defender"]]
            )
            p2 = CombatParticipant(Character("Mover"), 20, 20)

            tmap = TacticalMap(10, 10)
            p1.position = (5, 5)
            p2.position = (4, 5)
            p2.actions_remaining = 5
            tmap.set_occupant(*p1.position, p1)
            tmap.set_occupant(*p2.position, p2)

            engine = AvaCombatEngine([p1, p2], tmap)

            initial_hp = p2.current_hp
            engine.action_move(p2, 1, 5)

            return {
                "mover_hp": p2.current_hp,
                "mover_position": list(p2.position),
                "hp_changed": initial_hp != p2.current_hp
            }

        self._run_fixture("03_movement_oa", scenario)

    def test_04_status_effects(self):
        """Baseline: Hamstring applying SLOWED status."""
        def scenario():
            archer = Character("Archer")
            archer.base_stats["Intelligence"] = 3
            archer.base_skills["Intelligence"]["Perception"] = 2
            archer.base_stats["Dexterity"] = 2
            archer.base_skills["Dexterity"]["Finesse"] = 1

            p1 = CombatParticipant(
                archer, 20, 20,
                weapon_main=AVALORE_WEAPONS["Crossbow"],
                feats=[AVALORE_FEATS["Hamstring"]]
            )
            p2 = CombatParticipant(Character("Target"), 20, 20)

            tmap = TacticalMap(20, 20)
            p1.position = (0, 0)
            p2.position = (10, 0)
            p1.actions_remaining = 10
            tmap.set_occupant(*p1.position, p1)
            tmap.set_occupant(*p2.position, p2)

            engine = AvaCombatEngine([p1, p2], tmap)

            result = engine.action_hamstring(p1, p2, p1.weapon_main)
            has_slowed = p2.has_status(StatusEffect.SLOWED)

            return {
                "hit": result.get("result", {}).get("hit", False),
                "defender_has_slowed": has_slowed,
                "defender_hp": p2.current_hp
            }

        self._run_fixture("04_status_effects", scenario)

    def test_05_mighty_strike(self):
        """Baseline: Mighty Strike causing knockback."""
        def scenario():
            warrior = Character("Warrior")
            warrior.base_stats["Strength"] = 4
            warrior.base_skills["Strength"]["Athletics"] = 3

            p1 = CombatParticipant(
                warrior, 20, 20,
                weapon_main=AVALORE_WEAPONS["Greatsword"],
                feats=[AVALORE_FEATS["Mighty Strike"]]
            )
            p2 = CombatParticipant(Character("Target"), 20, 20)

            tmap = TacticalMap(15, 15)
            p1.position = (7, 7)
            p2.position = (8, 7)
            p1.actions_remaining = 10
            tmap.set_occupant(*p1.position, p1)
            tmap.set_occupant(*p2.position, p2)

            engine = AvaCombatEngine([p1, p2], tmap)

            initial_pos = p2.position
            result = engine.perform_attack(p1, p2, p1.weapon_main)

            return {
                "hit": result.get("hit", False),
                "defender_position": list(p2.position),
                "defender_hp": p2.current_hp,
                "position_changed": initial_pos != p2.position
            }

        self._run_fixture("05_mighty_strike", scenario)

    def test_06_multi_round(self):
        """Baseline: Multi-round combat with turn cycling."""
        def scenario():
            fighter1 = Character("Fighter1")
            fighter1.base_stats["Strength"] = 2
            fighter1.base_skills["Strength"]["Athletics"] = 1

            fighter2 = Character("Fighter2")
            fighter2.base_stats["Strength"] = 2
            fighter2.base_skills["Strength"]["Athletics"] = 1

            p1 = CombatParticipant(fighter1, 20, 20, weapon_main=AVALORE_WEAPONS["Arming Sword"])
            p2 = CombatParticipant(fighter2, 20, 20, weapon_main=AVALORE_WEAPONS["Arming Sword"])

            engine = AvaCombatEngine([p1, p2])
            engine.roll_initiative()

            p1.actions_remaining = 2
            engine.perform_attack(p1, p2, p1.weapon_main)
            engine.advance_turn()

            p2.actions_remaining = 2
            engine.perform_attack(p2, p1, p2.weapon_main)
            engine.advance_turn()

            p1.actions_remaining = 2
            engine.perform_attack(p1, p2, p1.weapon_main)

            return {
                "fighter1_hp": p1.current_hp,
                "fighter2_hp": p2.current_hp,
                "round_count": engine.round
            }

        self._run_fixture("06_multi_round", scenario)

    def test_07_terrain_cover(self):
        """Baseline: Forest terrain providing cover."""
        def scenario():
            p1 = CombatParticipant(Character("Archer"), 20, 20, weapon_main=AVALORE_WEAPONS["Longbow"])
            p2 = CombatParticipant(Character("Target"), 20, 20)

            tmap = TacticalMap(20, 20)
            p1.position = (0, 0)
            p2.position = (10, 0)
            tmap.set_occupant(*p1.position, p1)
            tmap.set_occupant(*p2.position, p2)

            tile = tmap.get_tile(10, 0)
            if tile:
                tile.terrain_type = TerrainType.FOREST

            p1.actions_remaining = 10
            engine = AvaCombatEngine([p1, p2], tmap)

            cover = tmap.cover_between(p1.position, p2.position)

            for _ in range(3):
                engine.perform_attack(p1, p2, p1.weapon_main)

            return {
                "cover_type": cover,
                "defender_hp": p2.current_hp
            }

        self._run_fixture("07_terrain_cover", scenario)

    def test_08_patient_flow(self):
        """Baseline: Patient Flow redirecting attacks."""
        def scenario():
            monk = Character("Monk")
            monk.base_stats["Dexterity"] = 3
            monk.base_skills["Dexterity"]["Acrobatics"] = 2

            p1 = CombatParticipant(
                monk, 20, 20,
                weapon_main=AVALORE_WEAPONS["Unarmed"],
                feats=[AVALORE_FEATS["Patient Flow"]]
            )
            p2 = CombatParticipant(Character("Attacker"), 20, 20, weapon_main=AVALORE_WEAPONS["Arming Sword"])
            p3 = CombatParticipant(Character("Bystander"), 20, 20)

            tmap = TacticalMap(10, 10)
            p1.position = (5, 5)
            p2.position = (4, 5)
            p3.position = (6, 5)
            p1.actions_remaining = 5
            p2.actions_remaining = 5

            tmap.set_occupant(*p1.position, p1)
            tmap.set_occupant(*p2.position, p2)
            tmap.set_occupant(*p3.position, p3)

            engine = AvaCombatEngine([p1, p2, p3], tmap)

            engine.action_patient_flow(p1)

            initial_p1_hp = p1.current_hp
            initial_p3_hp = p3.current_hp

            engine.perform_attack(p2, p1, p2.weapon_main)

            return {
                "monk_flowing": p1.flowing_stance,
                "monk_hp": p1.current_hp,
                "bystander_hp": p3.current_hp,
                "monk_took_damage": initial_p1_hp != p1.current_hp,
                "bystander_took_damage": initial_p3_hp != p3.current_hp
            }

        self._run_fixture("08_patient_flow", scenario)

    def test_09_control_knockback(self):
        """Baseline: Control feat knockback into wall."""
        def scenario():
            warrior = Character("Warrior")
            warrior.base_stats["Strength"] = 4
            warrior.base_skills["Strength"]["Athletics"] = 3

            p1 = CombatParticipant(
                warrior, 20, 20,
                weapon_main=AVALORE_WEAPONS["Greatsword"],
                feats=[AVALORE_FEATS["Control"]]
            )
            p2 = CombatParticipant(Character("Target"), 20, 20)

            tmap = TacticalMap(10, 10)
            p1.position = (5, 5)
            p2.position = (4, 5)
            p1.actions_remaining = 10

            for y in range(10):
                tile = tmap.get_tile(2, y)
                if tile:
                    tile.terrain_type = TerrainType.WALL
                    tile.passable = False

            tmap.set_occupant(*p1.position, p1)
            tmap.set_occupant(*p2.position, p2)

            engine = AvaCombatEngine([p1, p2], tmap)

            initial_hp = p2.current_hp
            initial_pos = p2.position

            result = engine.perform_attack(p1, p2, p1.weapon_main)

            return {
                "hit": result.get("hit", False),
                "defender_hp": p2.current_hp,
                "defender_position": list(p2.position),
                "damage_dealt": initial_hp - p2.current_hp
            }

        self._run_fixture("09_control_knockback", scenario)

    def test_10_full_combat(self):
        """Baseline: Full combat from initiative to defeat."""
        def scenario():
            fighter = Character("Fighter")
            fighter.base_stats["Strength"] = 4
            fighter.base_skills["Strength"]["Athletics"] = 3

            target = Character("Target")
            target.base_stats["Strength"] = 1
            target.base_skills["Strength"]["Athletics"] = 0

            p1 = CombatParticipant(fighter, 30, 30, weapon_main=AVALORE_WEAPONS["Greatsword"])
            p2 = CombatParticipant(target, 10, 10, weapon_main=AVALORE_WEAPONS["Arming Sword"])

            engine = AvaCombatEngine([p1, p2])
            engine.roll_initiative()

            turns = 0
            max_turns = 20

            while p1.current_hp > 0 and p2.current_hp > 0 and turns < max_turns:
                current = engine.get_current_participant()
                if current and current.current_hp > 0:
                    current.actions_remaining = 2
                    opponent = p2 if current == p1 else p1
                    if opponent.current_hp > 0:
                        engine.perform_attack(current, opponent, current.weapon_main)

                engine.advance_turn()
                turns += 1

            return {
                "fighter_alive": p1.current_hp > 0,
                "target_alive": p2.current_hp > 0,
                "fighter_hp": p1.current_hp,
                "target_hp": p2.current_hp,
                "turns_elapsed": turns
            }

        self._run_fixture("10_full_combat", scenario)


if __name__ == "__main__":
    # Suppress combat log output during tests
    import sys
    import io

    # Run tests
    unittest.main(verbosity=2)
