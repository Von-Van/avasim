"""
Batch simulation runner for Avalore Combat.

Run N combats with the same setup, collect statistics.

Usage:
    from combat.batch import BatchRunner, BatchConfig, BatchResult

    config = BatchConfig(
        participants_factory=lambda: [attacker(), defender()],
        map_factory=lambda ps: build_map(ps),
        num_combats=1000,
        strategy="balanced",
    )
    result = BatchRunner.run(config, progress_callback=lambda i, n: ...)
    print(result.summary())
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .engine import AvaCombatEngine
from .map import TacticalMap
from .participant import CombatParticipant
from .ai import CombatAI


@dataclass
class BatchConfig:
    """Configuration for a batch of combats.

    Parameters
    ----------
    participants_factory : callable
        Returns a fresh list of CombatParticipant for each combat.
        Each participant MUST have a ``team`` field set if you want
        meaningful win-rate stats.
    map_factory : callable or None
        Given the participant list, returns a TacticalMap (or None).
    num_combats : int
        How many combats to run.
    turn_limit : int
        Max turns per combat (safety valve).
    strategy : str
        AI strategy name ("balanced", "aggressive", "defensive").
    time_of_day : str
        "day" or "night".
    surprise : str
        "none", "surprised", or "ambush".
    """

    participants_factory: Callable[[], List[CombatParticipant]] = field(default=lambda: [])
    map_factory: Optional[Callable[[List[CombatParticipant]], Optional[TacticalMap]]] = None
    num_combats: int = 100
    turn_limit: int = 200
    strategy: str = "balanced"
    time_of_day: str = "day"
    surprise: str = "none"


@dataclass
class CombatRecord:
    """Stats for a single completed combat."""
    winner: str = ""
    rounds: int = 0
    total_damage: Dict[str, float] = field(default_factory=dict)
    survivor_hp: Dict[str, int] = field(default_factory=dict)


@dataclass
class BatchResult:
    """Aggregated statistics from a batch run."""
    records: List[CombatRecord] = field(default_factory=list)
    teams: List[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    @property
    def num_combats(self) -> int:
        return len(self.records)

    def win_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self.records:
            counts[r.winner] = counts.get(r.winner, 0) + 1
        return counts

    def win_rates(self) -> Dict[str, float]:
        n = max(1, self.num_combats)
        return {k: v / n for k, v in self.win_counts().items()}

    def avg_rounds(self) -> float:
        if not self.records:
            return 0.0
        return sum(r.rounds for r in self.records) / len(self.records)

    def avg_damage_by_team(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        for r in self.records:
            for team, dmg in r.total_damage.items():
                totals[team] = totals.get(team, 0.0) + dmg
                counts[team] = counts.get(team, 0) + 1
        return {team: totals[team] / max(1, counts[team]) for team in totals}

    def draws(self) -> int:
        return sum(1 for r in self.records if r.winner == "" or r.winner == "Draw")

    def summary(self) -> str:
        lines = [
            f"=== Batch Result: {self.num_combats} combats ===",
            f"Elapsed: {self.elapsed_seconds:.2f}s",
            f"Average rounds: {self.avg_rounds():.1f}",
        ]
        rates = self.win_rates()
        for team in sorted(rates, key=rates.get, reverse=True):  # type: ignore
            pct = rates[team] * 100
            lines.append(f"  {team}: {pct:.1f}% win rate ({self.win_counts()[team]} wins)")
        d = self.draws()
        if d:
            lines.append(f"  Draws: {d}")
        avg_dmg = self.avg_damage_by_team()
        if avg_dmg:
            lines.append("Average damage per combat:")
            for team in sorted(avg_dmg):
                lines.append(f"  {team}: {avg_dmg[team]:.1f}")
        return "\n".join(lines)


class BatchRunner:
    """Runs multiple combats and collects statistics."""

    @staticmethod
    def run(
        config: BatchConfig,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        result = BatchResult()
        t0 = time.time()

        # Discover teams from first batch of participants
        sample = config.participants_factory()
        result.teams = sorted({p.team for p in sample if p.team})

        for i in range(config.num_combats):
            participants = config.participants_factory()
            tmap = config.map_factory(participants) if config.map_factory else None
            record = BatchRunner._run_single(
                participants, tmap, config.turn_limit,
                config.strategy, config.time_of_day, config.surprise,
            )
            result.records.append(record)
            if progress_callback:
                progress_callback(i + 1, config.num_combats)

        result.elapsed_seconds = time.time() - t0
        return result

    @staticmethod
    def _run_single(
        participants: List[CombatParticipant],
        tmap: Optional[TacticalMap],
        turn_limit: int,
        strategy: str,
        time_of_day: str,
        surprise: str,
    ) -> CombatRecord:
        engine = AvaCombatEngine(participants, tactical_map=tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore
        engine.set_time_of_day(time_of_day)
        if surprise == "surprised":
            engine.party_surprised = True
        elif surprise == "ambush":
            engine.party_initiated = True

        # Track starting HP for damage calculation
        start_hp: Dict[str, int] = {}
        for p in participants:
            key = p.team or p.character.name
            start_hp[key] = start_hp.get(key, 0) + p.current_hp

        ai = CombatAI(strategy=strategy, show_decisions=False)

        engine.roll_initiative()
        turns = 0
        while not engine.is_combat_ended() and turns < turn_limit:
            current = engine.get_current_participant()
            if current is None or current.current_hp <= 0:
                engine.advance_turn()
                turns += 1
                continue
            ai.decide_turn(engine, current)
            engine.advance_turn()
            turns += 1

        # Calculate results
        record = CombatRecord()
        record.rounds = engine.round
        record.winner = engine.get_winning_team() or "Draw"

        # Total damage = start HP - remaining HP per team
        end_hp: Dict[str, int] = {}
        for p in participants:
            key = p.team or p.character.name
            end_hp[key] = end_hp.get(key, 0) + max(0, p.current_hp)

        # Damage dealt BY each team = total HP lost by opponents
        all_teams = set(start_hp.keys())
        for team in all_teams:
            opponent_lost = sum(
                start_hp.get(t, 0) - end_hp.get(t, 0)
                for t in all_teams if t != team
            )
            record.total_damage[team] = max(0.0, opponent_lost)

        for p in participants:
            key = p.team or p.character.name
            record.survivor_hp[key] = record.survivor_hp.get(key, 0) + max(0, p.current_hp)

        return record
