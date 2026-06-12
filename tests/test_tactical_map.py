#!/usr/bin/env python3
"""
Test script demonstrating the tactical map and movement system.
"""

import unittest
from dataclasses import dataclass
from typing import Dict, List
from combat import (
    AvaCombatEngine, CombatParticipant, TacticalMap,
    AVALORE_WEAPONS, AVALORE_ARMOR, AVALORE_FEATS, TerrainType
)


@dataclass
class MockCharacter:
    """Mock character for testing combat system."""
    name: str
    stats: Dict[str, int]
    skills: Dict[str, Dict[str, int]]
    feats: List[str]
    
    def get_stat(self, stat_name: str) -> int:
        return self.stats.get(stat_name, 0)
    
    def get_modifier(self, stat_name: str, skill_name: str) -> int:
        stat = self.stats.get(stat_name, 0)
        skill = self.skills.get(stat_name, {}).get(skill_name, 0)
        return stat + skill


def create_test_map(width=20, height=20):
    """Create a test tactical map with some terrain variety."""
    tmap = TacticalMap(width, height)
    
    # Add some forest tiles
    for x in range(5, 10):
        for y in range(5, 10):
            tile = tmap.get_tile(x, y)
            tile.terrain_type = TerrainType.FOREST
            tile.move_cost = 2
    
    # Add a wall
    for y in range(0, 15):
        tile = tmap.get_tile(10, y)
        tile.terrain_type = TerrainType.WALL
        tile.passable = False
    
    # Add a road for faster movement
    for x in range(0, 20):
        tile = tmap.get_tile(x, 15)
        tile.terrain_type = TerrainType.ROAD
        tile.move_cost = 0.5
    
    return tmap


def test_movement_and_pathfinding():
    """Test movement, pathfinding, and range checking."""
    print("=" * 60)
    print("TACTICAL MAP & MOVEMENT SYSTEM TEST")
    print("=" * 60)
    
    # Create mock characters
    warrior_char = MockCharacter(
        name="Warrior",
        stats={"Strength": 3, "Dexterity": 2, "Wisdom": 0, "Harmony": 0},
        skills={
            "Strength": {"Athletics": 2, "Fortitude": 1},
            "Dexterity": {"Acrobatics": 1, "Stealth": 0},
            "Wisdom": {},
            "Harmony": {}
        },
        feats=["Control", "Mighty Strike"]
    )
    
    archer_char = MockCharacter(
        name="Archer",
        stats={"Strength": 1, "Dexterity": 3, "Wisdom": 2, "Harmony": 0},
        skills={
            "Strength": {},
            "Dexterity": {"Acrobatics": 2, "Stealth": 1},
            "Wisdom": {"Perception": 2, "Survival": 0},
            "Harmony": {}
        },
        feats=["Always Ready", "Quickfooted"]
    )
    
    # Create tactical map
    tmap = create_test_map(20, 20)
    print("\n✓ Created 20x20 tactical map with terrain features")
    print("  - Forest area (5,5) to (9,9) - movement cost 2x")
    print("  - Wall at x=10, blocks movement")
    print("  - Road at y=15 - movement cost 0.5x")
    
    # Create combat participants with equipment
    warrior = CombatParticipant(
        character=warrior_char,
        current_hp=30,
        max_hp=30,
        weapon_main=AVALORE_WEAPONS["Polearm"],
        armor=AVALORE_ARMOR["Medium Armor"],
        shield=None,
        feats=[AVALORE_FEATS["Control"], AVALORE_FEATS["Mighty Strike"]],
        position=(2, 2)
    )
    
    archer = CombatParticipant(
        character=archer_char,
        current_hp=24,
        max_hp=24,
        weapon_main=AVALORE_WEAPONS["Longbow"],
        armor=AVALORE_ARMOR["Light Armor"],
        shield=None,
        feats=[AVALORE_FEATS["Always Ready"], AVALORE_FEATS["Quickfooted"]],
        position=(18, 18)
    )
    
    print("\n✓ Characters equipped:")
    print(f"  - {warrior.character.name}: {warrior.armor.name}, {warrior.weapon_main.name}")
    print(f"  - {archer.character.name}: {archer.armor.name}, {archer.weapon_main.name}")
    
    # Create combat with tactical map
    combat = AvaCombatEngine(
        participants=[warrior, archer],
        tactical_map=tmap
    )
    
    print("\n✓ Combat initialized with tactical map")
    print(f"  - {warrior.character.name} at position {warrior.position}")
    print(f"  - {archer.character.name} at position {archer.position}")
    
    # Test movement range calculation
    print("\n" + "=" * 60)
    print("MOVEMENT RANGE TEST")
    print("=" * 60)
    
    warrior_move_range = 5 + warrior.armor.movement_penalty if warrior.armor else 5
    reachable = tmap.get_reachable_tiles(
        warrior.position[0],
        warrior.position[1],
        warrior_move_range,
        warrior
    )
    
    print(f"\n{warrior.character.name} movement range: {warrior_move_range} blocks")
    print(f"Can reach {len(reachable)} tiles from position {warrior.position}")
    print(f"Sample reachable positions: {list(reachable)[:10]}")
    
    # Test pathfinding
    print("\n" + "=" * 60)
    print("PATHFINDING TEST")
    print("=" * 60)
    
    start_x, start_y = warrior.position
    dest_x, dest_y = 8, 8  # Inside the forest
    
    path = tmap.find_path(start_x, start_y, dest_x, dest_y, warrior)
    if path:
        print(f"\nPath from {(start_x, start_y)} to {(dest_x, dest_y)}:")
        print(f"  Length: {len(path)} steps")
        print(f"  Path: {path[:10]}{'...' if len(path) > 10 else ''}")
        
        # Calculate movement cost
        move_cost = 0
        for i in range(1, len(path)):
            x, y = path[i]
            tile = tmap.get_tile(x, y)
            move_cost += tile.move_cost
        print(f"  Total movement cost: {move_cost:.1f} blocks")
    else:
        print(f"\nNo path found from {(start_x, start_y)} to {(dest_x, dest_y)}")
    
    # Test actual movement
    print("\n" + "=" * 60)
    print("MOVEMENT ACTION TEST")
    print("=" * 60)
    
    print(f"\n{warrior.character.name} starting position: {warrior.position}")
    print(f"Actions: {warrior.actions_remaining}/2")
    
    # Try to move to a nearby position
    move_success = combat.action_move(warrior, 3, 3)
    print(f"Move to (3, 3): {'Success' if move_success else 'Failed'}")
    print(f"New position: {warrior.position}")
    print(f"Actions remaining: {warrior.actions_remaining}/2")
    
    # Test range checking
    print("\n" + "=" * 60)
    print("RANGE CHECKING TEST")
    print("=" * 60)
    
    distance = combat.get_distance(warrior, archer)
    spear_in_range = combat.is_in_range(warrior, archer, AVALORE_WEAPONS["Polearm"])
    longbow_in_range = combat.is_in_range(archer, warrior, AVALORE_WEAPONS["Longbow"])
    
    print(f"\nDistance between characters: {distance} blocks")
    print(f"Polearm (MELEE reach) in range: {spear_in_range}")
    print(f"Longbow (RANGED) in range: {longbow_in_range}")
    
    # Test knockback
    print("\n" + "=" * 60)
    print("KNOCKBACK TEST")
    print("=" * 60)
    
    print(f"\n{archer.character.name} position before knockback: {archer.position}")
    combat.apply_knockback(
        archer,
        blocks=3,
        source_pos=warrior.position,
        source_name=warrior.character.name
    )
    print(f"{archer.character.name} position after knockback: {archer.position}")
    
    # Test dash action
    print("\n" + "=" * 60)
    print("DASH ACTION TEST")
    print("=" * 60)
    
    # Reset actions
    warrior.actions_remaining = 2
    print(f"\n{warrior.character.name} actions: {warrior.actions_remaining}/2")
    
    dash_success = combat.action_dash(warrior, 5, 5)
    print(f"Dash to (5, 5): {'Success' if dash_success else 'Failed'}")
    print(f"New position: {warrior.position}")
    print(f"Actions remaining: {warrior.actions_remaining}/2")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


class TestTacticalMapAutomated(unittest.TestCase):
    def _participant(self, name: str, position: tuple[int, int]) -> CombatParticipant:
        character = MockCharacter(
            name=name,
            stats={"Strength": 3, "Dexterity": 2, "Intelligence": 0, "Harmony": 0},
            skills={
                "Strength": {"Athletics": 2, "Fortitude": 1, "Forging": 0},
                "Dexterity": {"Acrobatics": 1, "Stealth": 0, "Finesse": 0},
                "Intelligence": {"Healing": 0, "Perception": 0, "Research": 0},
                "Harmony": {"Arcana": 0, "Nature": 0, "Belief": 0},
            },
            feats=[],
        )
        return CombatParticipant(
            character=character,
            current_hp=20,
            max_hp=20,
            weapon_main=AVALORE_WEAPONS["Arming Sword"],
            armor=AVALORE_ARMOR["Light Armor"],
            position=position,
        )

    def test_pathfinding_avoids_impassable_wall(self):
        tmap = create_test_map(20, 20)
        actor = self._participant("Walker", (2, 2))
        path = tmap.find_path(2, 2, 8, 8, actor)

        self.assertIsNotNone(path)
        self.assertNotIn((10, 8), path)

    def test_action_move_updates_grid_occupant(self):
        tmap = create_test_map(20, 20)
        actor = self._participant("Walker", (2, 2))
        target = self._participant("Target", (18, 18))
        tmap.set_occupant(2, 2, actor)
        tmap.set_occupant(18, 18, target)
        combat = AvaCombatEngine([actor, target], tactical_map=tmap, capture_policy="summary")

        self.assertTrue(combat.action_move(actor, 3, 3))
        self.assertIsNone(tmap.get_occupant(2, 2))
        self.assertIs(tmap.get_occupant(3, 3), actor)
        self.assertEqual(actor.position, (3, 3))

    def test_knockback_changes_position_until_blocked(self):
        tmap = TacticalMap(8, 3)
        actor = self._participant("Attacker", (1, 1))
        target = self._participant("Target", (2, 1))
        tmap.set_occupant(1, 1, actor)
        tmap.set_occupant(2, 1, target)
        combat = AvaCombatEngine([actor, target], tactical_map=tmap, capture_policy="summary")

        moved, blocked = combat.apply_knockback(target, blocks=3, source_pos=actor.position, source_name=actor.character.name)
        self.assertTrue(moved)
        self.assertFalse(blocked)
        self.assertEqual(target.position, (5, 1))
        self.assertIs(tmap.get_occupant(5, 1), target)


if __name__ == "__main__":
    test_movement_and_pathfinding()
