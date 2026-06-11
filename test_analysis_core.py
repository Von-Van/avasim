import inspect
import unittest

from combat import (
    BatchRequest,
    CharacterBuild,
    ComparisonRequest,
    ExecutionOptions,
    RunRequest,
    ScenarioConfig,
    run,
    run_batch,
    compare,
)
from combat import factory


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


def make_build(name: str, team: str, weapon: str = "Arming Sword") -> CharacterBuild:
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


def make_request(seed: int = 42, capture_policy: str = "summary") -> RunRequest:
    return RunRequest(
        builds=[make_build("A", "Team A"), make_build("B", "Team B")],
        scenario=ScenarioConfig(width=6, height=6, positions=[[0, 0], [1, 0]]),
        seed=seed,
        execution=ExecutionOptions(
            capture_policy=capture_policy,
            default_ai_profile="aggressive",
            turn_limit=100,
        ),
    )


class TestAnalysisCore(unittest.TestCase):
    def test_identical_request_and_seed_are_deterministic(self):
        request = make_request(seed=77, capture_policy="replay")
        self.assertEqual(run(request).to_dict(), run(request).to_dict())

    def test_summary_and_replay_capture_policies(self):
        summary = run(make_request(seed=12, capture_policy="summary"))
        replay = run(make_request(seed=12, capture_policy="replay"))

        self.assertEqual(summary.winner, replay.winner)
        self.assertEqual(summary.rounds, replay.rounds)
        self.assertEqual([state.__dict__ for state in summary.participants],
                         [state.__dict__ for state in replay.participants])
        self.assertEqual(summary.events, [])
        self.assertEqual(summary.snapshots, [])
        self.assertGreater(len(replay.events), 0)
        self.assertGreater(len(replay.snapshots), 0)
        self.assertEqual([event["seq"] for event in replay.events], list(range(1, len(replay.events) + 1)))

    def test_batch_seeds_and_parallel_order_are_stable(self):
        request = make_request(seed=0)
        serial = run_batch(BatchRequest(request, num_runs=20, base_seed=100, parallelism=1, sample_replays=False))
        parallel = run_batch(BatchRequest(request, num_runs=20, base_seed=100, parallelism=4, sample_replays=False))

        self.assertEqual(serial.seeds, list(range(100, 120)))
        self.assertEqual([result.to_dict() for result in serial.results],
                         [result.to_dict() for result in parallel.results])

    def test_paired_comparison_uses_identical_seed_sets(self):
        request_a = make_request(seed=0)
        request_b = make_request(seed=999)
        request_b.builds[0].hand1 = "Mace"
        report = compare(ComparisonRequest(request_a, request_b, num_runs=8, base_seed=500, parallelism=1))

        self.assertEqual(report.left.seeds, report.right.seeds)
        self.assertEqual(report.deltas["paired_seeds"], list(range(500, 508)))

    def test_comparison_progress_counts_both_batches(self):
        progress = []
        compare(
            ComparisonRequest(make_request(seed=0), make_request(seed=1), num_runs=3, base_seed=10),
            progress_callback=lambda current, total: progress.append((current, total)),
        )

        self.assertEqual(progress, [(1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6)])

    def test_invalid_build_blocks_unless_override_is_explicit(self):
        invalid = make_request(seed=1)
        invalid.builds[0].hand1 = "Not A Real Weapon"

        blocked = run(invalid)
        self.assertTrue(blocked.blocked)
        self.assertEqual(blocked.outcome, "invalid")
        self.assertTrue(blocked.validation_issues)

        invalid.execution.allow_invalid_builds = True
        overridden = run(invalid)
        self.assertFalse(overridden.blocked)
        self.assertTrue(overridden.validation_issues)
        self.assertNotEqual(overridden.outcome, "invalid")

    def test_legacy_request_round_trips_through_contracts(self):
        legacy = {
            "char1": make_build("Legacy A", "Team A").to_legacy_template(),
            "char2": make_build("Legacy B", "Team B").to_legacy_template(),
            "scenario": {"width": 8, "height": 8, "attacker_pos": [0, 0], "defender_pos": [2, 0]},
            "surprise": "Party Ambushes",
            "config": {"strategy": "defensive", "capture_policy": "summary"},
            "seed": 321,
        }
        request = RunRequest.from_dict(legacy)
        round_tripped = RunRequest.from_dict(request.to_dict())

        self.assertEqual(round_tripped.to_dict(), request.to_dict())
        self.assertTrue(round_tripped.scenario.party_initiated)
        self.assertEqual(round_tripped.builds[0].name, "Legacy A")

    def test_representative_replay_matches_original_summary(self):
        request = make_request(seed=0)
        report = run_batch(BatchRequest(request, num_runs=12, base_seed=200, parallelism=1, sample_replays=True))
        summaries_by_seed = {result.seed: result for result in report.results}

        self.assertTrue(report.representative_replays)
        for seed, replay in report.representative_replays.items():
            summary = summaries_by_seed[seed]
            self.assertEqual(replay.outcome, summary.outcome)
            self.assertEqual(replay.winner, summary.winner)
            self.assertEqual(replay.rounds, summary.rounds)
            self.assertEqual([state.__dict__ for state in replay.participants],
                             [state.__dict__ for state in summary.participants])
            self.assertGreater(len(replay.snapshots), 0)

    def test_pure_factory_has_no_qt_dependency(self):
        self.assertNotIn("PySide", inspect.getsource(factory))


if __name__ == "__main__":
    unittest.main()
