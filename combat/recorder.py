"""Deterministic structured event and metric recording for combat runs."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional


class CombatRecorder:
    def __init__(self, participant_names: Iterable[str], capture_events: bool = True):
        self.capture_events = capture_events
        self.events: List[Dict[str, Any]] = []
        self.sequence = 0
        self.stats: Dict[str, Dict[str, int]] = {
            name: {
                "damage_dealt": 0,
                "damage_taken": 0,
                "healing_done": 0,
                "attacks": 0,
                "hits": 0,
                "criticals": 0,
                "kills": 0,
                "turns": 0,
            }
            for name in participant_names
        }
        self.defeat_causes: Counter[str] = Counter()
        self.last_damage_cause_by_target: Dict[str, str] = {}
        self.survival_curve: Dict[str, List[int]] = defaultdict(list)
        self._last_statuses: Dict[str, set[str]] = {}

    def record(self, event_type: str, round_num: int, **data: Any) -> None:
        if not self.capture_events:
            return
        self.sequence += 1
        self.events.append({
            "seq": self.sequence,
            "type": event_type,
            "round": round_num,
            "data": data,
        })

    def record_turn(self, round_num: int, actor: str) -> None:
        self.stats[actor]["turns"] += 1
        self.record("turn_started", round_num, actor=actor)

    def record_round(self, round_num: int, alive_by_team: Dict[str, int]) -> None:
        for team, alive in alive_by_team.items():
            self.survival_curve[team].append(alive)
        self.record("round_started", round_num, alive_by_team=alive_by_team)

    def record_attack(
        self,
        round_num: int,
        attacker: str,
        defender: str,
        weapon: str,
        result: Dict[str, Any],
        hp_before: int,
        hp_after: int,
        defender_defeated: bool,
    ) -> None:
        damage = max(0, hp_before - hp_after)
        self.stats[attacker]["attacks"] += 1
        if result.get("hit"):
            self.stats[attacker]["hits"] += 1
        if result.get("is_crit"):
            self.stats[attacker]["criticals"] += 1
        self.stats[attacker]["damage_dealt"] += damage
        self.stats[defender]["damage_taken"] += damage
        if damage > 0:
            self.last_damage_cause_by_target[defender] = f"{weapon} attack"
        if defender_defeated:
            cause = f"{weapon} attack"
            self.stats[attacker]["kills"] += 1
            self.defeat_causes[cause] += 1
        self.record(
            "attack",
            round_num,
            attacker=attacker,
            defender=defender,
            weapon=weapon,
            hit=bool(result.get("hit")),
            critical=bool(result.get("is_crit")),
            graze=bool(result.get("is_graze")),
            blocked=bool(result.get("blocked")),
            damage=damage,
            hp_before=hp_before,
            hp_after=hp_after,
        )

    def record_movement(
        self,
        round_num: int,
        actor: str,
        origin: tuple[int, int],
        destination: tuple[int, int],
        movement_type: str,
    ) -> None:
        self.record(
            "movement",
            round_num,
            actor=actor,
            origin=list(origin),
            destination=list(destination),
            movement_type=movement_type,
        )

    def record_healing(self, round_num: int, source: str, target: str, amount: int, cause: str) -> None:
        self.stats[source]["healing_done"] += max(0, amount)
        self.record("healing", round_num, source=source, target=target, amount=max(0, amount), cause=cause)

    def record_status_changes(self, round_num: int, participants: Iterable[Any]) -> None:
        for participant in participants:
            name = participant.character.name
            current = {status.name.lower() for status in participant.status_effects}
            if participant.is_critical:
                current.add("critical")
            if participant.is_dead:
                current.add("dead")
            previous = self._last_statuses.get(name, set())
            for status in sorted(current - previous):
                self.record("status_applied", round_num, target=name, status=status)
            for status in sorted(previous - current):
                self.record("status_removed", round_num, target=name, status=status)
            self._last_statuses[name] = current

    def participant_stats(self, name: str) -> Dict[str, int]:
        return dict(self.stats.get(name, {}))
