"""Canonical pure-Python simulation, batch, and comparison APIs."""

from __future__ import annotations

import math
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from typing import Any, Callable, Dict, List, Optional

from .ai import CombatAI
from .contracts import (
    BatchReport,
    BatchRequest,
    ComparisonReport,
    ComparisonRequest,
    ParticipantFinalState,
    RunRequest,
    RunResult,
)
from .dice import rng_scope
from .engine import AvaCombatEngine
from .factory import builds_to_participants, scenario_to_map
from .recorder import CombatRecorder
from .validation import has_errors, validate_build, validate_run_request, validate_scenario


ProgressCallback = Optional[Callable[[int, int], None]]
CancelCheck = Optional[Callable[[], bool]]


def _team_key(participant: Any) -> str:
    return participant.team or participant.character.name


def _alive_by_team(participants: List[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for participant in participants:
        if participant.current_hp > 0 and not participant.is_dead:
            counts[_team_key(participant)] += 1
    return dict(counts)


def run(request: RunRequest | Dict[str, Any]) -> RunResult:
    request = RunRequest.from_dict(request) if isinstance(request, dict) else request
    issues = validate_run_request(request)
    if has_errors(issues) and not request.execution.allow_invalid_builds:
        return RunResult(
            seed=request.seed,
            outcome="invalid",
            winner="",
            participants=[],
            metrics={},
            validation_issues=issues,
            blocked=True,
            metadata=dict(request.metadata),
        )

    participants = builds_to_participants(request.builds)
    tactical_map = scenario_to_map(request.scenario, participants)
    rng = random.Random(request.seed)
    capture_policy = request.execution.capture_policy
    recorder = CombatRecorder(
        [participant.character.name for participant in participants],
        capture_events=capture_policy in {"events", "replay"},
    )
    engine = AvaCombatEngine(
        participants,
        tactical_map=tactical_map,
        capture_policy=capture_policy,
        recorder=recorder,
        rng=rng,
        emit_stdout=False,
    )
    engine.set_time_of_day(request.scenario.time_of_day)
    engine.environment_underwater = request.scenario.underwater
    engine.party_initiated = request.scenario.party_initiated
    engine.party_surprised = request.scenario.party_surprised

    turns = 0
    with rng_scope(rng):
        engine.roll_initiative()
        recorder.record_round(engine.round, _alive_by_team(participants))
        recorder.record_status_changes(engine.round, participants)
        while not engine.is_combat_ended() and turns < request.execution.turn_limit:
            current = engine.get_current_participant()
            if current is None:
                break
            if current.current_hp <= 0:
                previous_round = engine.round
                engine.advance_turn()
                if engine.round != previous_round:
                    recorder.record_round(engine.round, _alive_by_team(participants))
                turns += 1
                continue

            recorder.record_turn(engine.round, current.character.name)
            profile_key = current.team or current.character.name
            profile = request.execution.ai_profiles_by_team.get(
                profile_key,
                request.execution.default_ai_profile,
            )
            CombatAI(strategy=profile, show_decisions=False).decide_turn(engine, current)
            recorder.record_status_changes(engine.round, participants)
            engine._log_map_state(f"End turn: {current.character.name}")
            previous_round = engine.round
            engine.advance_turn()
            if engine.round != previous_round:
                recorder.record_round(engine.round, _alive_by_team(participants))
            turns += 1

    winner = engine.get_winning_team()
    timed_out = not engine.is_combat_ended()
    outcome = "timeout" if timed_out else ("draw" if not winner else "victory")
    total_damage = sum(stats["damage_dealt"] for stats in recorder.stats.values())
    total_attacks = sum(stats["attacks"] for stats in recorder.stats.values())
    total_hits = sum(stats["hits"] for stats in recorder.stats.values())
    total_criticals = sum(stats["criticals"] for stats in recorder.stats.values())
    damage_by_team: Dict[str, int] = defaultdict(int)
    final_states: List[ParticipantFinalState] = []
    for participant in participants:
        name = participant.character.name
        stats = recorder.participant_stats(name)
        team = _team_key(participant)
        damage_by_team[team] += stats.get("damage_dealt", 0)
        defeat_cause = ""
        if participant.current_hp <= 0 or participant.is_dead:
            defeat_cause = recorder.last_damage_cause_by_target.get(name, "")
        final_states.append(
            ParticipantFinalState(
                name=name,
                team=participant.team,
                final_hp=participant.current_hp,
                max_hp=participant.max_hp,
                is_alive=participant.current_hp > 0 and not participant.is_dead,
                final_position=[participant.position[0], participant.position[1]],
                damage_dealt=stats.get("damage_dealt", 0),
                damage_taken=stats.get("damage_taken", 0),
                healing_done=stats.get("healing_done", 0),
                kills=stats.get("kills", 0),
                turns_taken=stats.get("turns", 0),
                status_effects=sorted(status.name.lower() for status in participant.status_effects),
                defeat_cause=defeat_cause,
            )
        )

    metrics = {
        "total_rounds": engine.round,
        "total_turns": turns,
        "total_damage": total_damage,
        "total_attacks": total_attacks,
        "total_hits": total_hits,
        "total_criticals": total_criticals,
        "hit_rate": total_hits / total_attacks if total_attacks else 0.0,
        "critical_rate": total_criticals / total_attacks if total_attacks else 0.0,
        "average_damage_per_hit": total_damage / total_hits if total_hits else 0.0,
        "damage_by_team": dict(damage_by_team),
        "survival_curve": dict(recorder.survival_curve),
        "defeat_causes": dict(recorder.defeat_causes),
    }
    return RunResult(
        seed=request.seed,
        outcome=outcome,
        winner=winner or ("Draw" if outcome == "draw" else ""),
        participants=final_states,
        metrics=metrics,
        validation_issues=issues,
        events=list(recorder.events),
        snapshots=list(engine.map_snapshots),
        combat_log=list(engine.combat_log),
        metadata=dict(request.metadata),
    )


def _wilson_interval(wins: int, total: int, z: float = 1.96) -> List[float]:
    if total <= 0:
        return [0.0, 0.0]
    p = wins / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def _aggregate(results: List[RunResult]) -> Dict[str, Any]:
    count = len(results)
    wins = Counter(result.winner or result.outcome.title() for result in results)
    win_rates = {winner: value / count for winner, value in wins.items()} if count else {}
    intervals = {winner: _wilson_interval(value, count) for winner, value in wins.items()}
    damage_totals: Dict[str, float] = defaultdict(float)
    survival_totals: Dict[str, int] = defaultdict(int)
    ending_hp_totals: Dict[str, int] = defaultdict(int)
    participant_counts: Dict[str, int] = defaultdict(int)
    defeat_causes: Counter[str] = Counter()
    survival_curves: Dict[str, List[float]] = {}
    curve_values: Dict[str, List[List[int]]] = defaultdict(list)
    for result in results:
        for team, damage in result.metrics.get("damage_by_team", {}).items():
            damage_totals[team] += damage
        for team, curve in result.metrics.get("survival_curve", {}).items():
            curve_values[team].append(curve)
        for participant in result.participants:
            team = participant.team or participant.name
            participant_counts[team] += 1
            ending_hp_totals[team] += participant.final_hp
            if participant.is_alive:
                survival_totals[team] += 1
            if participant.defeat_cause:
                defeat_causes[participant.defeat_cause] += 1
    for team, curves in curve_values.items():
        max_length = max((len(curve) for curve in curves), default=0)
        survival_curves[team] = [
            sum(curve[index] if index < len(curve) else curve[-1] for curve in curves if curve) / max(1, len(curves))
            for index in range(max_length)
        ]
    return {
        "win_counts": dict(wins),
        "win_rates": win_rates,
        "win_rate_intervals": intervals,
        "draws": sum(1 for result in results if result.outcome == "draw"),
        "timeouts": sum(1 for result in results if result.outcome == "timeout"),
        "average_rounds": sum(result.rounds for result in results) / count if count else 0.0,
        "round_distribution": dict(Counter(result.rounds for result in results)),
        "average_damage_by_team": {team: value / count for team, value in damage_totals.items()} if count else {},
        "survival_rates": {team: survival_totals[team] / participant_counts[team] for team in participant_counts},
        "average_ending_hp": {team: ending_hp_totals[team] / participant_counts[team] for team in participant_counts},
        "survival_curves": survival_curves,
        "common_defeat_causes": dict(defeat_causes),
        "overall_hit_rate": (
            sum(result.metrics.get("total_hits", 0) for result in results)
            / max(1, sum(result.metrics.get("total_attacks", 0) for result in results))
        ),
        "overall_critical_rate": (
            sum(result.metrics.get("total_criticals", 0) for result in results)
            / max(1, sum(result.metrics.get("total_attacks", 0) for result in results))
        ),
    }


def _representative_seeds(results: List[RunResult]) -> List[int]:
    selected: List[int] = []
    by_outcome: Dict[str, RunResult] = {}
    for result in results:
        key = result.winner or result.outcome
        by_outcome.setdefault(key, result)
    selected.extend(result.seed for result in list(by_outcome.values())[:2])
    if results:
        selected.append(max(results, key=lambda result: (result.rounds, -result.seed)).seed)
    return list(dict.fromkeys(selected))


def run_batch(
    request: BatchRequest | Dict[str, Any],
    progress_callback: ProgressCallback = None,
    cancel_check: CancelCheck = None,
) -> BatchReport:
    request = BatchRequest.from_dict(request) if isinstance(request, dict) else request
    seeds = [request.base_seed + index for index in range(request.num_runs)]
    started = time.perf_counter()

    def execute(seed: int) -> RunResult:
        return run(request.run_request.with_seed(seed, capture_policy="summary"))

    results: List[RunResult] = []
    cancelled = False
    if request.parallelism > 1:
        with ThreadPoolExecutor(max_workers=request.parallelism) as executor:
            for index, result in enumerate(executor.map(execute, seeds), start=1):
                results.append(result)
                if progress_callback:
                    progress_callback(index, len(seeds))
                if cancel_check and cancel_check():
                    cancelled = True
                    break
    else:
        for index, seed in enumerate(seeds, start=1):
            if cancel_check and cancel_check():
                cancelled = True
                break
            results.append(execute(seed))
            if progress_callback:
                progress_callback(index, len(seeds))

    replay_results: Dict[int, RunResult] = {}
    if request.sample_replays and not cancelled:
        for seed in _representative_seeds(results):
            replay_results[seed] = run(request.run_request.with_seed(seed, capture_policy="replay"))
    return BatchReport(
        seeds=seeds[:len(results)],
        results=results,
        aggregate=_aggregate(results),
        representative_replays=replay_results,
        elapsed_seconds=time.perf_counter() - started,
        cancelled=cancelled,
    )


def compare(
    request: ComparisonRequest | Dict[str, Any],
    progress_callback: ProgressCallback = None,
    cancel_check: CancelCheck = None,
) -> ComparisonReport:
    if isinstance(request, dict):
        request = ComparisonRequest(
            left=RunRequest.from_dict(request["left"]),
            right=RunRequest.from_dict(request["right"]),
            num_runs=int(request.get("num_runs", 100)),
            base_seed=int(request.get("base_seed", 0)),
            parallelism=int(request.get("parallelism", 1)),
        )
    def left_progress(current: int, total: int) -> None:
        if progress_callback:
            progress_callback(current, total * 2)

    def right_progress(current: int, total: int) -> None:
        if progress_callback:
            progress_callback(total + current, total * 2)

    left = run_batch(
        BatchRequest(request.left, request.num_runs, request.base_seed, request.parallelism, sample_replays=False),
        progress_callback=left_progress,
        cancel_check=cancel_check,
    )
    right = run_batch(
        BatchRequest(request.right, request.num_runs, request.base_seed, request.parallelism, sample_replays=False),
        progress_callback=right_progress,
        cancel_check=cancel_check,
    )
    teams = set(left.win_rates()) | set(right.win_rates())
    damage_teams = set(left.avg_damage_by_team()) | set(right.avg_damage_by_team())
    deltas = {
        "win_rate_delta": {team: right.win_rates().get(team, 0.0) - left.win_rates().get(team, 0.0) for team in teams},
        "damage_delta": {team: right.avg_damage_by_team().get(team, 0.0) - left.avg_damage_by_team().get(team, 0.0) for team in damage_teams},
        "average_rounds_delta": right.avg_rounds() - left.avg_rounds(),
        "paired_seeds": list(left.seeds),
    }
    return ComparisonReport(left=left, right=right, deltas=deltas)


__all__ = [
    "compare",
    "run",
    "run_batch",
    "validate_build",
    "validate_scenario",
]
