"""
Tests for Phase 2.2 (multi-combatant / teams) and Phase 2.3 (batch simulation).
"""

import unittest
from combat import (
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
    AVALORE_WEAPONS,
    AVALORE_ARMOR,
    AVALORE_FEATS,
    BatchRunner,
    BatchConfig,
    BatchResult,
)
from combat.ai import CombatAI
from avasim import Character


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_participant(name: str, hp: int = 20, team: str = "",
                      weapon: str = "Arming Sword") -> CombatParticipant:
    char = Character(name)
    char.base_stats["Strength"] = 2
    char.base_skills["Strength"]["Athletics"] = 1
    p = CombatParticipant(
        char, hp, hp,
        weapon_main=AVALORE_WEAPONS[weapon],
        team=team,
    )
    return p


def _make_map(width: int = 10, height: int = 10) -> TacticalMap:
    return TacticalMap(width, height)


def _place(tmap: TacticalMap, participant: CombatParticipant, x: int, y: int):
    participant.position = (x, y)
    tmap.set_occupant(x, y, participant)


# ===========================================================================
# Phase 2.2 – Team / Multi-combatant engine tests
# ===========================================================================


class TestTeamField(unittest.TestCase):
    """Verify the team field on CombatParticipant."""

    def test_default_team_empty(self):
        p = _make_participant("Solo")
        self.assertEqual(p.team, "")

    def test_team_assignment(self):
        p = _make_participant("Knight", team="Team A")
        self.assertEqual(p.team, "Team A")


class TestTeamCombatEnded(unittest.TestCase):
    """is_combat_ended and get_winning_team with teams."""

    def test_two_teams_one_alive(self):
        """Combat ends when only one team has survivors."""
        p1 = _make_participant("A1", team="Alpha")
        p2 = _make_participant("B1", team="Beta")
        p2.current_hp = 0
        p2.is_dead = True
        engine = AvaCombatEngine([p1, p2])
        self.assertTrue(engine.is_combat_ended())
        self.assertEqual(engine.get_winning_team(), "Alpha")

    def test_two_teams_both_alive(self):
        """Combat continues when both teams have survivors."""
        p1 = _make_participant("A1", team="Alpha")
        p2 = _make_participant("B1", team="Beta")
        engine = AvaCombatEngine([p1, p2])
        self.assertFalse(engine.is_combat_ended())

    def test_three_participants_two_teams(self):
        """2v1 scenario: combat ends only when one team is wiped."""
        p1 = _make_participant("A1", team="Alpha")
        p2 = _make_participant("A2", team="Alpha")
        p3 = _make_participant("B1", team="Beta")
        engine = AvaCombatEngine([p1, p2, p3])
        self.assertFalse(engine.is_combat_ended())

        p3.current_hp = 0
        p3.is_dead = True
        self.assertTrue(engine.is_combat_ended())
        self.assertEqual(engine.get_winning_team(), "Alpha")

    def test_ffa_no_teams(self):
        """FFA (no teams): combat ends when ≤1 alive."""
        p1 = _make_participant("A")
        p2 = _make_participant("B")
        p3 = _make_participant("C")
        engine = AvaCombatEngine([p1, p2, p3])
        self.assertFalse(engine.is_combat_ended())

        p2.current_hp = 0
        p2.is_dead = True
        self.assertFalse(engine.is_combat_ended())  # 2 alive, no teams

        p3.current_hp = 0
        p3.is_dead = True
        self.assertTrue(engine.is_combat_ended())  # 1 alive

    def test_mixed_teams_and_ffa(self):
        """Some participants have teams, some don't."""
        p1 = _make_participant("A1", team="Alpha")
        p2 = _make_participant("Loner")  # No team
        p3 = _make_participant("B1", team="Beta")
        engine = AvaCombatEngine([p1, p2, p3])
        self.assertFalse(engine.is_combat_ended())

        p3.current_hp = 0
        p3.is_dead = True
        # Alpha is only team alive, but Loner (no team) is still alive
        self.assertFalse(engine.is_combat_ended())

    def test_all_dead_draw(self):
        """All dead → combat ended, no winner."""
        p1 = _make_participant("A1", team="Alpha")
        p2 = _make_participant("B1", team="Beta")
        p1.current_hp = 0
        p1.is_dead = True
        p2.current_hp = 0
        p2.is_dead = True
        engine = AvaCombatEngine([p1, p2])
        self.assertTrue(engine.is_combat_ended())
        self.assertEqual(engine.get_winning_team(), "")

    def test_get_combat_summary_includes_team(self):
        """Summary should include team tags."""
        p1 = _make_participant("Knight", team="Alpha")
        p2 = _make_participant("Rogue", team="Beta")
        p2.current_hp = 0
        p2.is_dead = True
        engine = AvaCombatEngine([p1, p2])
        summary = engine.get_combat_summary()
        self.assertIn("[Alpha]", summary)
        self.assertIn("[Beta]", summary)
        self.assertIn("Winner: Alpha", summary)


class TestAITeamTargeting(unittest.TestCase):
    """AI correctly targets enemies, not allies."""

    def test_ai_targets_enemy_not_ally(self):
        """AI on Team A should target Team B, not Team A."""
        p1 = _make_participant("A1", team="Alpha")
        p2 = _make_participant("A2", team="Alpha")
        p3 = _make_participant("B1", team="Beta")
        tmap = _make_map()
        _place(tmap, p1, 0, 0)
        _place(tmap, p2, 1, 0)
        _place(tmap, p3, 2, 0)
        engine = AvaCombatEngine([p1, p2, p3], tactical_map=tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore

        ai = CombatAI(strategy="balanced")
        target = ai._pick_target(engine, p1)
        self.assertIs(target, p3, "Should target enemy, not ally")

    def test_ai_no_target_all_allies(self):
        """When all others are allies, no target found."""
        p1 = _make_participant("A1", team="Alpha")
        p2 = _make_participant("A2", team="Alpha")
        tmap = _make_map()
        _place(tmap, p1, 0, 0)
        _place(tmap, p2, 1, 0)
        engine = AvaCombatEngine([p1, p2], tactical_map=tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore

        ai = CombatAI(strategy="balanced")
        target = ai._pick_target(engine, p1)
        self.assertIsNone(target, "No enemies = no target")

    def test_ffa_targets_everyone(self):
        """FFA (no teams): everyone is a valid target."""
        p1 = _make_participant("A")
        p2 = _make_participant("B")
        p3 = _make_participant("C")
        tmap = _make_map()
        _place(tmap, p1, 0, 0)
        _place(tmap, p2, 1, 0)
        _place(tmap, p3, 5, 0)
        engine = AvaCombatEngine([p1, p2, p3], tactical_map=tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore

        ai = CombatAI(strategy="balanced")
        target = ai._pick_target(engine, p1)
        self.assertIsNotNone(target)
        # Should pick nearest (p2)
        self.assertIs(target, p2)


# ===========================================================================
# Phase 2.2 – N-participant full combat
# ===========================================================================


class TestMultiCombatantCombat(unittest.TestCase):
    """Run full combat with >2 participants."""

    def test_three_way_ffa(self):
        """3-way FFA runs to completion."""
        p1 = _make_participant("A", hp=15)
        p2 = _make_participant("B", hp=15)
        p3 = _make_participant("C", hp=15)
        tmap = _make_map()
        _place(tmap, p1, 0, 0)
        _place(tmap, p2, 1, 0)
        _place(tmap, p3, 2, 0)
        engine = AvaCombatEngine([p1, p2, p3], tactical_map=tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore
        engine.roll_initiative()

        ai = CombatAI(strategy="aggressive")
        turns = 0
        while not engine.is_combat_ended() and turns < 100:
            current = engine.get_current_participant()
            if current is None or current.current_hp <= 0:
                engine.advance_turn()
                turns += 1
                continue
            ai.decide_turn(engine, current)
            engine.advance_turn()
            turns += 1

        alive = [p for p in [p1, p2, p3] if p.current_hp > 0]
        self.assertLessEqual(len(alive), 1, "FFA should end with 0 or 1 alive")

    def test_two_vs_one(self):
        """2v1 team combat: the team of 2 should usually win."""
        p1 = _make_participant("A1", hp=20, team="Alpha")
        p2 = _make_participant("A2", hp=20, team="Alpha")
        p3 = _make_participant("B1", hp=20, team="Beta")
        tmap = _make_map()
        _place(tmap, p1, 0, 0)
        _place(tmap, p2, 1, 0)
        _place(tmap, p3, 3, 0)
        engine = AvaCombatEngine([p1, p2, p3], tactical_map=tmap)
        engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore
        engine.roll_initiative()

        ai = CombatAI(strategy="balanced")
        turns = 0
        while not engine.is_combat_ended() and turns < 200:
            current = engine.get_current_participant()
            if current is None or current.current_hp <= 0:
                engine.advance_turn()
                turns += 1
                continue
            ai.decide_turn(engine, current)
            engine.advance_turn()
            turns += 1

        self.assertTrue(engine.is_combat_ended())
        winner = engine.get_winning_team()
        # Winner should be a string (team or name)
        self.assertTrue(len(winner) > 0, f"Expected a winner, got '{winner}'")


# ===========================================================================
# Phase 2.3 – Batch simulation
# ===========================================================================


class TestBatchRunner(unittest.TestCase):
    """Test BatchRunner.run() and result statistics."""

    def _participants_factory(self):
        p1 = _make_participant("Fighter", hp=20, team="Team A")
        p2 = _make_participant("Rogue", hp=18, team="Team B")
        return [p1, p2]

    def _map_factory(self, participants):
        tmap = _make_map(10, 10)
        _place(tmap, participants[0], 0, 0)
        _place(tmap, participants[1], 3, 0)
        return tmap

    def test_batch_runs(self):
        """Batch runner completes N combats."""
        config = BatchConfig(
            participants_factory=self._participants_factory,
            map_factory=self._map_factory,
            num_combats=10,
            turn_limit=100,
            strategy="balanced",
        )
        result = BatchRunner.run(config)
        self.assertEqual(result.num_combats, 10)
        self.assertEqual(len(result.records), 10)
        self.assertGreater(result.elapsed_seconds, 0)

    def test_batch_win_rates(self):
        """Win rates sum to ~1.0."""
        config = BatchConfig(
            participants_factory=self._participants_factory,
            map_factory=self._map_factory,
            num_combats=20,
            turn_limit=100,
        )
        result = BatchRunner.run(config)
        rates = result.win_rates()
        total = sum(rates.values())
        self.assertAlmostEqual(total, 1.0, places=2,
                               msg=f"Win rates should sum to 1.0, got {total}")

    def test_batch_avg_rounds(self):
        """Average rounds is a positive number."""
        config = BatchConfig(
            participants_factory=self._participants_factory,
            map_factory=self._map_factory,
            num_combats=10,
            turn_limit=100,
        )
        result = BatchRunner.run(config)
        self.assertGreater(result.avg_rounds(), 0)

    def test_batch_summary(self):
        """Summary string contains expected fields."""
        config = BatchConfig(
            participants_factory=self._participants_factory,
            map_factory=self._map_factory,
            num_combats=5,
        )
        result = BatchRunner.run(config)
        summary = result.summary()
        self.assertIn("Batch Result", summary)
        self.assertIn("5 combats", summary)
        self.assertIn("win rate", summary)

    def test_batch_progress_callback(self):
        """Progress callback is called for each combat."""
        progress = []
        config = BatchConfig(
            participants_factory=self._participants_factory,
            map_factory=self._map_factory,
            num_combats=5,
        )
        result = BatchRunner.run(config, progress_callback=lambda i, n: progress.append((i, n)))
        self.assertEqual(len(progress), 5)
        self.assertEqual(progress[-1], (5, 5))

    def test_batch_avg_damage(self):
        """Average damage by team is non-negative."""
        config = BatchConfig(
            participants_factory=self._participants_factory,
            map_factory=self._map_factory,
            num_combats=10,
            turn_limit=100,
        )
        result = BatchRunner.run(config)
        avg_dmg = result.avg_damage_by_team()
        for team, dmg in avg_dmg.items():
            self.assertGreaterEqual(dmg, 0, f"Team {team} avg damage should be ≥ 0")

    def test_batch_no_map(self):
        """Batch works without a tactical map."""
        config = BatchConfig(
            participants_factory=self._participants_factory,
            map_factory=None,
            num_combats=5,
            turn_limit=100,
        )
        result = BatchRunner.run(config)
        self.assertEqual(result.num_combats, 5)

    def test_batch_multi_combatant(self):
        """Batch with 3+ combatants across 2 teams."""
        def factory():
            return [
                _make_participant("A1", hp=20, team="Alpha"),
                _make_participant("A2", hp=20, team="Alpha"),
                _make_participant("B1", hp=25, team="Beta"),
            ]

        def mfactory(ps):
            tmap = _make_map()
            _place(tmap, ps[0], 0, 0)
            _place(tmap, ps[1], 1, 0)
            _place(tmap, ps[2], 4, 0)
            return tmap

        config = BatchConfig(
            participants_factory=factory,
            map_factory=mfactory,
            num_combats=10,
            turn_limit=150,
        )
        result = BatchRunner.run(config)
        self.assertEqual(result.num_combats, 10)
        # Should have teams Alpha and Beta
        self.assertIn("Alpha", result.teams)
        self.assertIn("Beta", result.teams)


class TestBatchResult(unittest.TestCase):
    """Test BatchResult statistics."""

    def test_empty_result(self):
        result = BatchResult()
        self.assertEqual(result.num_combats, 0)
        self.assertEqual(result.avg_rounds(), 0.0)
        self.assertEqual(result.win_counts(), {})
        self.assertEqual(result.win_rates(), {})
        self.assertEqual(result.draws(), 0)

    def test_draws_counted(self):
        from combat.batch import CombatRecord
        result = BatchResult(records=[
            CombatRecord(winner="Alpha", rounds=5),
            CombatRecord(winner="Draw", rounds=10),
            CombatRecord(winner="", rounds=8),
        ])
        self.assertEqual(result.draws(), 2)


if __name__ == "__main__":
    unittest.main()
