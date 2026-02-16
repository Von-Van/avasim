"""
Generate baseline fixture scenarios from current Python engine.

Each fixture captures:
- Input: seed, character builds, positions, environment
- Output: final HP, positions, status effects, turn count
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from combat import (
    AvaCombatEngine, CombatParticipant, TacticalMap, TerrainType,
    AVALORE_WEAPONS, AVALORE_ARMOR, AVALORE_SHIELDS, AVALORE_FEATS,
    StatusEffect, set_seed
)
from avasim import Character


def run_combat_fixture(scenario_func, seed: int, name: str, description: str):
    """Run a scenario and capture the outcome."""
    set_seed(seed)

    result = scenario_func()

    fixture = {
        "name": name,
        "description": description,
        "seed": seed,
        "input": result["input"],
        "expected_output": result["output"]
    }

    return fixture


def fixture_01_basic_melee():
    """Basic melee combat: warrior vs target."""
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

    # Perform 3 attacks
    for _ in range(3):
        engine.perform_attack(p1, p2, p1.weapon_main)

    return {
        "input": {
            "attacker": {
                "name": "Warrior",
                "strength": 3,
                "athletics": 2,
                "weapon": "Arming Sword",
                "position": [5, 5]
            },
            "defender": {
                "name": "Target",
                "position": [6, 5]
            },
            "actions": ["attack", "attack", "attack"]
        },
        "output": {
            "defender_hp": p2.current_hp,
            "defender_max_hp": p2.max_hp,
            "attacker_actions_used": 10 - p1.actions_remaining
        }
    }


def fixture_02_ranged_los():
    """Ranged combat with line of sight."""
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

    # Fire 2 shots
    engine.perform_attack(p1, p2, p1.weapon_main)
    engine.perform_attack(p1, p2, p1.weapon_main)

    return {
        "input": {
            "attacker": {"name": "Archer", "weapon": "Longbow", "position": [0, 5]},
            "defender": {"position": [15, 5]},
            "actions": ["attack", "attack"]
        },
        "output": {
            "defender_hp": p2.current_hp,
            "attacker_actions_remaining": p1.actions_remaining
        }
    }


def fixture_03_movement_oa():
    """Movement triggering opportunity attack."""
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
    # Move out of reach
    engine.action_move(p2, 1, 5)

    return {
        "input": {
            "defender": {"weapon": "Polearm", "feats": ["Steadfast Defender"], "position": [5, 5]},
            "mover": {"initial_hp": initial_hp, "position": [4, 5]},
            "action": "move to [1, 5]"
        },
        "output": {
            "mover_hp": p2.current_hp,
            "mover_position": list(p2.position),
            "hp_changed": initial_hp != p2.current_hp
        }
    }


def fixture_04_status_effects():
    """Hamstring applying SLOWED status."""
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
        "input": {
            "attacker": {"feats": ["Hamstring"], "weapon": "Crossbow"},
            "defender": {}
        },
        "output": {
            "hit": result.get("result", {}).get("hit", False),
            "defender_has_slowed": has_slowed,
            "defender_hp": p2.current_hp
        }
    }


def fixture_05_mighty_strike():
    """Mighty Strike causing knockback."""
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
        "input": {
            "attacker": {"feats": ["Mighty Strike"], "weapon": "Greatsword", "position": [7, 7]},
            "defender": {"initial_position": list(initial_pos)}
        },
        "output": {
            "hit": result.get("hit", False),
            "defender_position": list(p2.position),
            "defender_hp": p2.current_hp,
            "position_changed": initial_pos != p2.position
        }
    }


def fixture_06_multi_round():
    """Multi-round combat with turn cycling."""
    fighter1 = Character("Fighter1")
    fighter1.base_stats["Strength"] = 2
    fighter1.base_skills["Strength"]["Athletics"] = 1

    fighter2 = Character("Fighter2")
    fighter2.base_stats["Strength"] = 2
    fighter2.base_skills["Strength"]["Athletics"] = 1

    p1 = CombatParticipant(fighter1, 20, 20, weapon_main=AVALORE_WEAPONS["Arming Sword"])
    p2 = CombatParticipant(fighter2, 20, 20, weapon_main=AVALORE_WEAPONS["Arming Sword"])

    engine = AvaCombatEngine([p1, p2])

    # Initialize combat
    engine.roll_initiative()

    # Play several turns manually
    p1.actions_remaining = 2
    engine.perform_attack(p1, p2, p1.weapon_main)
    engine.advance_turn()

    p2.actions_remaining = 2
    engine.perform_attack(p2, p1, p2.weapon_main)
    engine.advance_turn()

    # Second round
    p1.actions_remaining = 2
    engine.perform_attack(p1, p2, p1.weapon_main)

    return {
        "input": {
            "combatants": 2,
            "turns": 3
        },
        "output": {
            "fighter1_hp": p1.current_hp,
            "fighter2_hp": p2.current_hp,
            "round_count": engine.round
        }
    }


def fixture_07_terrain_cover():
    """Forest terrain providing cover."""
    p1 = CombatParticipant(Character("Archer"), 20, 20, weapon_main=AVALORE_WEAPONS["Longbow"])
    p2 = CombatParticipant(Character("Target"), 20, 20)

    tmap = TacticalMap(20, 20)
    p1.position = (0, 0)
    p2.position = (10, 0)
    tmap.set_occupant(*p1.position, p1)
    tmap.set_occupant(*p2.position, p2)

    # Target in forest
    tile = tmap.get_tile(10, 0)
    if tile:
        tile.terrain_type = TerrainType.FOREST

    p1.actions_remaining = 10
    engine = AvaCombatEngine([p1, p2], tmap)

    cover = tmap.cover_between(p1.position, p2.position)

    # 3 attacks
    for _ in range(3):
        engine.perform_attack(p1, p2, p1.weapon_main)

    return {
        "input": {
            "attacker": {"position": [0, 0]},
            "defender": {"position": [10, 0], "terrain": "forest"}
        },
        "output": {
            "cover_type": cover,
            "defender_hp": p2.current_hp
        }
    }


def fixture_08_patient_flow():
    """Patient Flow redirecting attacks."""
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

    # Activate Patient Flow
    engine.action_patient_flow(p1)

    initial_p1_hp = p1.current_hp
    initial_p3_hp = p3.current_hp

    # p2 attacks p1
    engine.perform_attack(p2, p1, p2.weapon_main)

    return {
        "input": {
            "monk": {"feats": ["Patient Flow"], "position": [5, 5]},
            "attacker": {"position": [4, 5]},
            "bystander": {"position": [6, 5]}
        },
        "output": {
            "monk_flowing": p1.flowing_stance,
            "monk_hp": p1.current_hp,
            "bystander_hp": p3.current_hp,
            "monk_took_damage": initial_p1_hp != p1.current_hp,
            "bystander_took_damage": initial_p3_hp != p3.current_hp
        }
    }


def fixture_09_control_knockback():
    """Control feat knockback into wall."""
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

    # Wall to the left
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
        "input": {
            "attacker": {"feats": ["Control"], "weapon": "Greatsword", "position": [5, 5]},
            "defender": {"position": [4, 5]},
            "wall_at": "x=2"
        },
        "output": {
            "hit": result.get("hit", False),
            "defender_hp": p2.current_hp,
            "defender_position": list(p2.position),
            "damage_dealt": initial_hp - p2.current_hp
        }
    }


def fixture_10_full_combat():
    """Full combat from initiative to defeat."""
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

    # Simple combat loop: alternate attacks
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
        "input": {
            "fighter": {"hp": 30, "strength": 4},
            "target": {"hp": 10}
        },
        "output": {
            "fighter_alive": p1.current_hp > 0,
            "target_alive": p2.current_hp > 0,
            "fighter_hp": p1.current_hp,
            "target_hp": p2.current_hp,
            "turns_elapsed": turns
        }
    }


def main():
    """Generate all 10 fixtures."""
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [
        (fixture_01_basic_melee, 12345, "01_basic_melee", "Basic melee attack sequence"),
        (fixture_02_ranged_los, 23456, "02_ranged_los", "Ranged combat with line of sight"),
        (fixture_03_movement_oa, 34567, "03_movement_oa", "Movement triggering opportunity attack"),
        (fixture_04_status_effects, 45678, "04_status_effects", "Hamstring applying SLOWED status"),
        (fixture_05_mighty_strike, 56789, "05_mighty_strike", "Mighty Strike knockback"),
        (fixture_06_multi_round, 67890, "06_multi_round", "Multi-round combat"),
        (fixture_07_terrain_cover, 78901, "07_terrain_cover", "Forest terrain cover bonus"),
        (fixture_08_patient_flow, 89012, "08_patient_flow", "Patient Flow attack redirection"),
        (fixture_09_control_knockback, 90123, "09_control_knockback", "Control knockback into wall"),
        (fixture_10_full_combat, 11111, "10_full_combat", "Full combat to defeat"),
    ]

    for scenario_func, seed, name, description in scenarios:
        print(f"Generating {name}...")
        fixture = run_combat_fixture(scenario_func, seed, name, description)

        output_path = fixtures_dir / f"{name}.json"
        with open(output_path, 'w') as f:
            json.dump(fixture, f, indent=2)

        print(f"  ✓ Saved to {output_path}")

    print(f"\n✅ Generated {len(scenarios)} fixtures in {fixtures_dir}")


if __name__ == "__main__":
    main()
