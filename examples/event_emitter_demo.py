#!/usr/bin/env python3
"""
Demonstration of EventEmitter for structured event output.

This script shows how to use the EventEmitter to convert combat engine
actions into structured events that match the @avasim/schema RunEvent format.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from combat import EventEmitter, set_seed

def main():
    """Demo the EventEmitter with a simple mock combat scenario."""

    # Create an event emitter
    emitter = EventEmitter(run_id="demo-run-001", seed=12345, engine_version="0.1.0-python")

    # Emit run start
    emitter.emit_run_started(participants=["Warrior", "Goblin"])

    # Emit round 1
    emitter.emit_round_started(round_num=1, turn_order=["Warrior", "Goblin"])

    # Warrior's turn
    emitter.emit_turn_started(actor="Warrior", actions_available=2, turn_index=0)

    # Warrior attacks Goblin
    emitter.emit_attack(
        attacker="Warrior",
        defender="Goblin",
        weapon="longsword",
        attack_roll=15,
        dice_values=(7, 8),
        defense_value=12,
        hit=True,
        critical=False,
        modifiers=[
            {"name": "Might bonus", "value": 2},
            {"name": "Weapon skill", "value": 1}
        ]
    )

    # Damage dealt
    emitter.emit_damage(
        source="Warrior",
        target="Goblin",
        damage_type="slashing",
        damage_amount=8,
        damage_mitigated=2,
        hp_before=12,
        hp_after=4
    )

    emitter.emit_turn_ended(actor="Warrior", actions_used=2)

    # Goblin's turn
    emitter.emit_turn_started(actor="Goblin", actions_available=2, turn_index=1)

    # Goblin moves
    emitter.emit_movement(
        actor="Goblin",
        from_pos=(3, 3),
        to_pos=(5, 3),
        distance=2,
        opportunity_attacks=[]
    )

    # Goblin attacks back (misses)
    emitter.emit_attack(
        attacker="Goblin",
        defender="Warrior",
        weapon="shortbow",
        attack_roll=10,
        dice_values=(5, 5),
        defense_value=14,
        hit=False
    )

    emitter.emit_turn_ended(actor="Goblin", actions_used=2)

    # End round 1
    emitter.emit_round_ended(survivors=["Warrior", "Goblin"])

    # Round 2 - Warrior finishes the goblin
    emitter.emit_round_started(round_num=2, turn_order=["Warrior", "Goblin"])
    emitter.emit_turn_started(actor="Warrior", actions_available=2, turn_index=0)

    # Feat activation
    emitter.emit_feat_activation(
        actor="Warrior",
        feat_name="Mighty Strike",
        effect_description="Next attack deals +4 damage",
        target="Goblin"
    )

    # Final attack
    emitter.emit_attack(
        attacker="Warrior",
        defender="Goblin",
        weapon="longsword",
        attack_roll=17,
        dice_values=(8, 9),
        defense_value=12,
        hit=True
    )

    # Lethal damage
    emitter.emit_damage(
        source="Warrior",
        target="Goblin",
        damage_type="slashing",
        damage_amount=12,
        damage_mitigated=2,
        hp_before=4,
        hp_after=0
    )

    # Death
    emitter.emit_death(character="Goblin", killer="Warrior")

    emitter.emit_turn_ended(actor="Warrior", actions_used=2)

    # Run completed
    emitter.emit_run_completed(outcome="victory", winning_team="party", total_rounds=2)

    # Output events
    print("=" * 70)
    print("EventEmitter Demo - Structured Event Output")
    print("=" * 70)
    print()
    print(f"Total events emitted: {len(emitter.get_events())}")
    print()
    print("Sample events:")
    print()

    for i, event in enumerate(emitter.get_events()[:5], 1):
        print(f"{i}. [{event['type']}] {event['message']}")

    print()
    print("..." + f" ({len(emitter.get_events()) - 5} more events)" if len(emitter.get_events()) > 5 else "")
    print()
    print("=" * 70)
    print("Full JSON output:")
    print("=" * 70)
    print(emitter.get_events_json())
    print()
    print("✅ Events are now compatible with @avasim/schema RunEvent format!")
    print("   These can be streamed via SSE to the orchestrator's event endpoint.")


if __name__ == "__main__":
    main()
