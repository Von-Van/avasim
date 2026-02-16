"""
Event adapter for converting combat engine logs to structured events.

This module provides an EventEmitter class that converts the Python combat
engine's log messages into structured RunEvent format that matches the
@avasim/schema contract.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
import json


class EventEmitter:
    """
    Converts combat engine actions into structured events.

    Usage:
        emitter = EventEmitter(run_id="abc-123", seed=12345)
        emitter.emit_run_started(participants=["Warrior", "Goblin"])
        emitter.emit_attack(attacker="Warrior", defender="Goblin", ...)

        # Get all events
        events = emitter.get_events()
    """

    def __init__(self, run_id: str, seed: int, engine_version: str = "0.1.0-python"):
        self.run_id = run_id
        self.seed = seed
        self.engine_version = engine_version
        self.events: List[Dict[str, Any]] = []
        self.current_round = 0
        self.current_turn_index: Optional[int] = None

    def _create_base_event(
        self,
        event_type: str,
        message: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a base event structure."""
        event = {
            "event_id": str(uuid4()),
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "round": self.current_round,
            "message": message,
            "data": data
        }

        if self.current_turn_index is not None:
            event["turn_index"] = self.current_turn_index

        return event

    def emit(self, event: Dict[str, Any]) -> None:
        """Emit an event to the event list."""
        self.events.append(event)

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all emitted events."""
        return self.events

    def get_events_json(self) -> str:
        """Get all events as JSON string."""
        return json.dumps(self.events, indent=2)

    # ========================================================================
    # Run lifecycle events
    # ========================================================================

    def emit_run_started(self, participants: List[str]) -> None:
        """Emit a run_started event."""
        event = self._create_base_event(
            event_type="run_started",
            message=f"Run started with seed {self.seed}",
            data={
                "run_id": self.run_id,
                "seed": self.seed,
                "engine_version": self.engine_version,
                "participants": participants
            }
        )
        self.emit(event)

    def emit_run_completed(
        self,
        outcome: str,
        winning_team: Optional[str] = None,
        total_rounds: Optional[int] = None
    ) -> None:
        """Emit a run_completed event."""
        if total_rounds is None:
            total_rounds = self.current_round

        event = self._create_base_event(
            event_type="run_completed",
            message=f"Run completed - {outcome}",
            data={
                "run_id": self.run_id,
                "outcome": outcome,
                "winning_team": winning_team,
                "total_rounds": total_rounds
            }
        )
        self.emit(event)

    # ========================================================================
    # Round and turn events
    # ========================================================================

    def emit_round_started(self, round_num: int, turn_order: List[str]) -> None:
        """Emit a round_started event."""
        self.current_round = round_num
        event = self._create_base_event(
            event_type="round_started",
            message=f"Round {round_num} begins",
            data={
                "round": round_num,
                "turn_order": turn_order
            }
        )
        self.emit(event)

    def emit_round_ended(self, survivors: List[str]) -> None:
        """Emit a round_ended event."""
        event = self._create_base_event(
            event_type="round_ended",
            message=f"Round {self.current_round} ended",
            data={
                "round": self.current_round,
                "survivors": survivors
            }
        )
        self.emit(event)

    def emit_turn_started(self, actor: str, actions_available: int, turn_index: int) -> None:
        """Emit a turn_started event."""
        self.current_turn_index = turn_index
        event = self._create_base_event(
            event_type="turn_started",
            message=f"{actor}'s turn ({actions_available} actions available)",
            data={
                "actor": actor,
                "actions_available": actions_available
            }
        )
        self.emit(event)

    def emit_turn_ended(self, actor: str, actions_used: int) -> None:
        """Emit a turn_ended event."""
        event = self._create_base_event(
            event_type="turn_ended",
            message=f"{actor}'s turn ended ({actions_used} actions used)",
            data={
                "actor": actor,
                "actions_used": actions_used
            }
        )
        self.emit(event)
        self.current_turn_index = None

    # ========================================================================
    # Combat action events
    # ========================================================================

    def emit_action(
        self,
        actor: str,
        action_type: str,
        action_cost: int,
        target: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit a generic action event."""
        msg = f"{actor} uses {action_type}"
        if target:
            msg += f" on {target}"

        event = self._create_base_event(
            event_type="action",
            message=msg,
            data={
                "actor": actor,
                "action_type": action_type,
                "action_cost": action_cost,
                "target": target,
                "details": details or {}
            }
        )
        self.emit(event)

    def emit_attack(
        self,
        attacker: str,
        defender: str,
        weapon: Optional[str],
        attack_roll: int,
        dice_values: Tuple[int, int],
        defense_value: int,
        hit: bool,
        critical: bool = False,
        modifiers: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Emit an attack event."""
        result = "CRITICAL HIT!" if critical else ("HIT!" if hit else "MISS")
        weapon_str = f" with {weapon}" if weapon else ""

        msg = f"{attacker} attacks {defender}{weapon_str} (roll: {attack_roll} vs {defense_value}) - {result}"

        event = self._create_base_event(
            event_type="attack",
            message=msg,
            data={
                "attacker": attacker,
                "defender": defender,
                "weapon": weapon,
                "attack_roll": attack_roll,
                "dice_values": list(dice_values),
                "defense_value": defense_value,
                "hit": hit,
                "critical": critical,
                "modifiers": modifiers or []
            }
        )
        self.emit(event)

    def emit_damage(
        self,
        source: str,
        target: str,
        damage_type: str,
        damage_amount: int,
        damage_mitigated: int,
        hp_before: int,
        hp_after: int,
        temp_hp_absorbed: int = 0
    ) -> None:
        """Emit a damage event."""
        actual_damage = damage_amount - damage_mitigated
        msg = f"{target} takes {actual_damage} {damage_type} damage"

        if damage_mitigated > 0:
            msg += f" ({damage_mitigated} absorbed by armor)"
        if temp_hp_absorbed > 0:
            msg += f" ({temp_hp_absorbed} absorbed by temp HP)"

        msg += f" -> {hp_after} HP"

        event = self._create_base_event(
            event_type="damage",
            message=msg,
            data={
                "source": source,
                "target": target,
                "damage_type": damage_type,
                "damage_amount": damage_amount,
                "damage_mitigated": damage_mitigated,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "temp_hp_absorbed": temp_hp_absorbed
            }
        )
        self.emit(event)

    def emit_healing(
        self,
        source: str,
        target: str,
        healing_amount: int,
        hp_before: int,
        hp_after: int
    ) -> None:
        """Emit a healing event."""
        event = self._create_base_event(
            event_type="healing",
            message=f"{target} heals for {healing_amount} HP -> {hp_after} HP",
            data={
                "source": source,
                "target": target,
                "healing_amount": healing_amount,
                "hp_before": hp_before,
                "hp_after": hp_after
            }
        )
        self.emit(event)

    def emit_movement(
        self,
        actor: str,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
        distance: int,
        opportunity_attacks: Optional[List[str]] = None
    ) -> None:
        """Emit a movement event."""
        msg = f"{actor} moves from {from_pos} to {to_pos} - distance {distance}"

        if opportunity_attacks:
            msg += f" (provokes OA from {', '.join(opportunity_attacks)})"

        event = self._create_base_event(
            event_type="movement",
            message=msg,
            data={
                "actor": actor,
                "from": list(from_pos),
                "to": list(to_pos),
                "distance": distance,
                "opportunity_attacks": opportunity_attacks or []
            }
        )
        self.emit(event)

    def emit_status_effect(
        self,
        target: str,
        effect: str,
        applied: bool,
        duration: Optional[int] = None,
        source: Optional[str] = None
    ) -> None:
        """Emit a status_effect event."""
        action = "applies" if applied else "removes"
        source_str = f"{source} " if source else ""
        duration_str = f" (duration: {duration} rounds)" if duration else ""

        msg = f"{source_str}{action} {effect} to {target}{duration_str}"

        event = self._create_base_event(
            event_type="status_effect",
            message=msg,
            data={
                "target": target,
                "effect": effect,
                "applied": applied,
                "duration": duration,
                "source": source
            }
        )
        self.emit(event)

    def emit_feat_activation(
        self,
        actor: str,
        feat_name: str,
        effect_description: str,
        target: Optional[str] = None
    ) -> None:
        """Emit a feat_activation event."""
        msg = f"{actor} activates {feat_name}"
        if target:
            msg += f" on {target}"

        event = self._create_base_event(
            event_type="feat_activation",
            message=msg,
            data={
                "actor": actor,
                "feat_name": feat_name,
                "target": target,
                "effect_description": effect_description
            }
        )
        self.emit(event)

    def emit_spell_cast(
        self,
        caster: str,
        spell_name: str,
        anima_cost: int,
        result: str,
        targets: Optional[List[str]] = None
    ) -> None:
        """Emit a spell_cast event."""
        msg = f"{caster} casts {spell_name} (cost: {anima_cost} anima)"
        if targets:
            msg += f" targeting {', '.join(targets)}"

        event = self._create_base_event(
            event_type="spell_cast",
            message=msg,
            data={
                "caster": caster,
                "spell_name": spell_name,
                "anima_cost": anima_cost,
                "targets": targets or [],
                "result": result
            }
        )
        self.emit(event)

    def emit_death(
        self,
        character: str,
        killer: Optional[str] = None,
        death_save_failures: int = 0
    ) -> None:
        """Emit a death event."""
        if killer:
            msg = f"{character} has been slain by {killer}"
        else:
            msg = f"{character} has died"

        event = self._create_base_event(
            event_type="death",
            message=msg,
            data={
                "character": character,
                "killer": killer,
                "death_save_failures": death_save_failures
            }
        )
        self.emit(event)

    def emit_map_snapshot(
        self,
        label: str,
        width: int,
        height: int,
        cells: List[Dict[str, Any]],
        actor: Optional[Dict[str, Any]] = None,
        target: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit a map_snapshot event."""
        event = self._create_base_event(
            event_type="map_snapshot",
            message=f"Map snapshot: {label}",
            data={
                "label": label,
                "width": width,
                "height": height,
                "cells": cells,
                "actor": actor,
                "target": target
            }
        )
        self.emit(event)
