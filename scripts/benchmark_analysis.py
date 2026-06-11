#!/usr/bin/env python3
"""Benchmark the canonical pure-Python analysis boundary."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from combat import BatchRequest, CharacterBuild, ExecutionOptions, RunRequest, ScenarioConfig, run_batch


BASE_STATS = {
    "Dexterity": 1,
    "Intelligence": 0,
    "Harmony": 0,
    "Strength": 2,
}

BASE_SKILLS = {
    "Dexterity": {"Acrobatics": 1, "Stealth": 0, "Finesse": 1},
    "Intelligence": {"Healing": 0, "Perception": 0, "Research": 0},
    "Harmony": {"Arcana": 0, "Nature": 0, "Belief": 0},
    "Strength": {"Athletics": 2, "Fortitude": 1, "Forging": 0},
}


def build(name: str, team: str, weapon: str = "Arming Sword") -> CharacterBuild:
    return CharacterBuild(
        name=name,
        team=team,
        current_hp=20,
        stats=dict(BASE_STATS),
        skills={stat: dict(skills) for stat, skills in BASE_SKILLS.items()},
        hand1=weapon,
        hand2="(None)",
        armor="Light Armor",
    )


def benchmark(runs: int, seed: int, parallelism: int) -> dict:
    request = RunRequest(
        builds=[build("Duelist A", "Team A"), build("Duelist B", "Team B")],
        scenario=ScenarioConfig(width=6, height=6, positions=[[0, 0], [1, 0]]),
        seed=seed,
        execution=ExecutionOptions(
            capture_policy="summary",
            default_ai_profile="aggressive",
            turn_limit=100,
        ),
    )
    batch = BatchRequest(
        run_request=request,
        num_runs=runs,
        base_seed=seed,
        parallelism=parallelism,
        sample_replays=False,
    )
    started = time.perf_counter()
    report = run_batch(batch)
    elapsed = time.perf_counter() - started
    return {
        "runs": report.num_combats,
        "seconds": round(elapsed, 4),
        "runs_per_second": round(report.num_combats / elapsed, 2) if elapsed else None,
        "average_rounds": round(report.avg_rounds(), 4),
        "win_rates": report.win_rates(),
        "base_seed": seed,
        "parallelism": parallelism,
        "sample_replays": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark AvaSim canonical analysis batches.")
    parser.add_argument("--runs", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--parallelism", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(benchmark(args.runs, args.seed, max(1, args.parallelism)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
