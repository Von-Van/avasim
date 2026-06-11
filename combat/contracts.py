"""Canonical Python contracts for reproducible AvaSim analysis runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Dict, List, Optional

from avasim import STATS


SCHEMA_VERSION = "1.0.0"
ENGINE_VERSION = "1.0.0-python"
CAPTURE_POLICIES = {"summary", "events", "replay"}


def _default_stats() -> Dict[str, int]:
    return {stat: 0 for stat in STATS}


def _default_skills() -> Dict[str, Dict[str, int]]:
    return {stat: {skill: 0 for skill in skills} for stat, skills in STATS.items()}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    severity: str
    message: str


@dataclass
class CharacterBuild:
    name: str
    stats: Dict[str, int] = field(default_factory=_default_stats)
    skills: Dict[str, Dict[str, int]] = field(default_factory=_default_skills)
    current_hp: int = 20
    max_hp: Optional[int] = None
    anima: int = 0
    max_anima: int = 0
    hand1: str = "Arming Sword"
    hand2: str = "(None)"
    armor: str = "None"
    feats: List[str] = field(default_factory=list)
    spells: List[str] = field(default_factory=list)
    primary_discipline: str = ""
    team: str = ""
    creature_type: str = "Unknown"
    lineage_weapon: Optional[str] = None
    lineage_weapon_alt: Optional[str] = None
    lineage_elements: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], default_name: str = "Combatant") -> "CharacterBuild":
        if isinstance(data, CharacterBuild):
            return data

        stats = _default_stats()
        raw_stats = data.get("stats") or data.get("base_stats") or {}
        for stat in stats:
            if stat in raw_stats:
                stats[stat] = int(raw_stats[stat])

        skills = _default_skills()
        raw_skills = data.get("skills") or data.get("base_skills") or {}
        for stat, stat_skills in skills.items():
            for skill in stat_skills:
                if skill in raw_skills.get(stat, {}):
                    skills[stat][skill] = int(raw_skills[stat][skill])

        hp_value = data.get("hp", data.get("current_hp", 20))
        if isinstance(hp_value, dict):
            current_hp = int(hp_value.get("current", hp_value.get("max", 20)))
            max_hp = int(hp_value["max"]) if hp_value.get("max") is not None else None
        else:
            current_hp = int(hp_value)
            max_hp = int(data["max_hp"]) if data.get("max_hp") is not None else None

        equipment = data.get("equipment") or {}
        hand1 = (
            data.get("hand1")
            or data.get("weapon")
            or equipment.get("weapon_main")
            or "Arming Sword"
        )
        hand2 = (
            data.get("hand2")
            or data.get("shield")
            or equipment.get("weapon_offhand")
            or equipment.get("shield")
            or "(None)"
        )
        armor = data.get("armor") or equipment.get("armor") or "None"
        lineage = data.get("lineage") or {}
        team = str(data.get("team", ""))
        if team == "FFA":
            team = ""

        return cls(
            name=str(data.get("name") or default_name),
            stats=stats,
            skills=skills,
            current_hp=current_hp,
            max_hp=max_hp,
            anima=int(data.get("anima", 0)),
            max_anima=int(data.get("max_anima", 0)),
            hand1=str(hand1),
            hand2=str(hand2),
            armor=str(armor),
            feats=[str(name) for name in data.get("feats", [])],
            spells=[str(name) for name in data.get("spells", [])],
            primary_discipline=str(data.get("primary_discipline", "")),
            team=team,
            creature_type=str(data.get("creature_type", "Unknown")),
            lineage_weapon=data.get("lineage_weapon", lineage.get("weapon")),
            lineage_weapon_alt=data.get("lineage_weapon_alt", lineage.get("weapon_alt")),
            lineage_elements=list(data.get("lineage_elements", lineage.get("elements", []))),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_legacy_template(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "hp": self.current_hp,
            "anima": self.anima,
            "max_anima": self.max_anima,
            "stats": self.stats,
            "skills": self.skills,
            "hand1": self.hand1,
            "hand2": self.hand2,
            "armor": self.armor,
            "team": self.team or "FFA",
            "feats": list(self.feats),
        }


@dataclass
class TerrainCell:
    x: int
    y: int
    terrain: str
    height: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TerrainCell":
        return cls(
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            terrain=str(data.get("terrain", "normal")).lower(),
            height=int(data.get("height", 0)),
        )


@dataclass
class ScenarioConfig:
    width: int = 10
    height: int = 10
    terrain: List[TerrainCell] = field(default_factory=list)
    positions: List[List[int]] = field(default_factory=list)
    time_of_day: str = "day"
    underwater: bool = False
    party_initiated: bool = False
    party_surprised: bool = False
    name: str = ""
    objectives: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ScenarioConfig":
        if isinstance(data, ScenarioConfig):
            return data
        data = data or {}
        positions = data.get("positions") or []
        if not positions:
            attacker = data.get("attacker_pos", [0, 0])
            defender = data.get("defender_pos", [3, 0])
            positions = [attacker, defender]
        environment = data.get("environment") or {}
        return cls(
            width=int(data.get("width", 10)),
            height=int(data.get("height", 10)),
            terrain=[TerrainCell.from_dict(cell) for cell in data.get("terrain", data.get("cells", []))],
            positions=[[int(pos[0]), int(pos[1])] for pos in positions],
            time_of_day=str(data.get("time_of_day", data.get("time", environment.get("time_of_day", "day")))).lower(),
            underwater=bool(data.get("underwater", environment.get("underwater", False))),
            party_initiated=bool(data.get("party_initiated", environment.get("party_initiated", False))),
            party_surprised=bool(data.get("party_surprised", environment.get("party_surprised", False))),
            name=str(data.get("name", "")),
            objectives=list(data.get("objectives", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionOptions:
    turn_limit: int = 200
    capture_policy: str = "replay"
    default_ai_profile: str = "balanced"
    ai_profiles_by_team: Dict[str, str] = field(default_factory=dict)
    allow_invalid_builds: bool = False

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ExecutionOptions":
        if isinstance(data, ExecutionOptions):
            return data
        data = data or {}
        capture = str(data.get("capture_policy", "replay"))
        if capture not in CAPTURE_POLICIES:
            capture = "replay"
        return cls(
            turn_limit=int(data.get("turn_limit", data.get("max_turns", 200))),
            capture_policy=capture,
            default_ai_profile=str(data.get("default_ai_profile", data.get("strategy", "balanced"))),
            ai_profiles_by_team=dict(data.get("ai_profiles_by_team", {})),
            allow_invalid_builds=bool(data.get("allow_invalid_builds", False)),
        )


@dataclass
class RunRequest:
    builds: List[CharacterBuild]
    scenario: ScenarioConfig = field(default_factory=ScenarioConfig)
    seed: int = 0
    version: str = SCHEMA_VERSION
    execution: ExecutionOptions = field(default_factory=ExecutionOptions)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunRequest":
        if isinstance(data, RunRequest):
            return data
        raw_builds = data.get("builds") or data.get("participants") or data.get("combatants") or []
        if not raw_builds and (data.get("char1") or data.get("char2")):
            raw_builds = [data.get("char1", {}), data.get("char2", {})]
        builds = [
            CharacterBuild.from_dict(build, default_name=f"Character {index + 1}")
            for index, build in enumerate(raw_builds)
        ]
        scenario = ScenarioConfig.from_dict(data.get("scenario") or data.get("map") or {})
        if data.get("surprise") == "Party Surprised":
            scenario.party_surprised = True
        elif data.get("surprise") == "Party Ambushes":
            scenario.party_initiated = True
        return cls(
            version=str(data.get("version", data.get("schema_version", SCHEMA_VERSION))),
            seed=int(data.get("seed", 0)),
            builds=builds,
            scenario=scenario,
            execution=ExecutionOptions.from_dict(data.get("execution") or data.get("config")),
            metadata=dict(data.get("metadata", {})),
        )

    def with_seed(self, seed: int, capture_policy: Optional[str] = None) -> "RunRequest":
        execution = replace(
            self.execution,
            capture_policy=capture_policy or self.execution.capture_policy,
        )
        return replace(self, seed=seed, execution=execution)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParticipantFinalState:
    name: str
    team: str
    final_hp: int
    max_hp: int
    is_alive: bool
    final_position: List[int]
    damage_dealt: int = 0
    damage_taken: int = 0
    healing_done: int = 0
    kills: int = 0
    turns_taken: int = 0
    status_effects: List[str] = field(default_factory=list)
    defeat_cause: str = ""


@dataclass
class RunResult:
    seed: int
    outcome: str
    winner: str
    participants: List[ParticipantFinalState]
    metrics: Dict[str, Any]
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    snapshots: List[Dict[str, Any]] = field(default_factory=list)
    combat_log: List[str] = field(default_factory=list)
    blocked: bool = False
    engine_version: str = ENGINE_VERSION
    schema_version: str = SCHEMA_VERSION
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def rounds(self) -> int:
        return int(self.metrics.get("total_rounds", 0))

    @property
    def total_damage(self) -> Dict[str, int]:
        return dict(self.metrics.get("damage_by_team", {}))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BatchRequest:
    run_request: RunRequest
    num_runs: int = 100
    base_seed: int = 0
    parallelism: int = 1
    sample_replays: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchRequest":
        if isinstance(data, BatchRequest):
            return data
        run_request = RunRequest.from_dict(data.get("run_request") or data)
        return cls(
            run_request=run_request,
            num_runs=int(data.get("num_runs", 100)),
            base_seed=int(data.get("base_seed", run_request.seed)),
            parallelism=max(1, int(data.get("parallelism", 1))),
            sample_replays=bool(data.get("sample_replays", True)),
        )


@dataclass
class BatchReport:
    seeds: List[int]
    results: List[RunResult]
    aggregate: Dict[str, Any]
    representative_replays: Dict[int, RunResult] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    cancelled: bool = False

    @property
    def records(self) -> List[RunResult]:
        return self.results

    @property
    def num_combats(self) -> int:
        return len(self.results)

    def win_counts(self) -> Dict[str, int]:
        return dict(self.aggregate.get("win_counts", {}))

    def win_rates(self) -> Dict[str, float]:
        return dict(self.aggregate.get("win_rates", {}))

    def avg_rounds(self) -> float:
        return float(self.aggregate.get("average_rounds", 0.0))

    def avg_damage_by_team(self) -> Dict[str, float]:
        return dict(self.aggregate.get("average_damage_by_team", {}))

    def summary(self) -> str:
        lines = [
            f"=== Analysis Report: {self.num_combats} combats ===",
            f"Elapsed: {self.elapsed_seconds:.2f}s",
            f"Average rounds: {self.avg_rounds():.2f}",
        ]
        intervals = self.aggregate.get("win_rate_intervals", {})
        for team, rate in sorted(self.win_rates().items(), key=lambda item: item[1], reverse=True):
            low, high = intervals.get(team, [rate, rate])
            lines.append(
                f"  {team}: {rate * 100:.1f}% win rate "
                f"(95% CI {low * 100:.1f}-{high * 100:.1f}%)"
            )
        lines.append(f"Draws: {self.aggregate.get('draws', 0)}")
        lines.append(f"Timeouts: {self.aggregate.get('timeouts', 0)}")
        damage = self.avg_damage_by_team()
        if damage:
            lines.append("Average damage per combat:")
            for team, value in sorted(damage.items()):
                lines.append(f"  {team}: {value:.2f}")
        causes = self.aggregate.get("common_defeat_causes", {})
        if causes:
            lines.append("Common defeat causes:")
            for cause, count in sorted(causes.items(), key=lambda item: (-item[1], item[0]))[:5]:
                lines.append(f"  {cause}: {count}")
        if self.representative_replays:
            lines.append("Representative replay seeds: " + ", ".join(map(str, self.representative_replays)))
        if self.cancelled:
            lines.append("Batch cancelled before all requested runs completed.")
        return "\n".join(lines)


@dataclass
class ComparisonRequest:
    left: RunRequest
    right: RunRequest
    num_runs: int = 100
    base_seed: int = 0
    parallelism: int = 1


@dataclass
class ComparisonReport:
    left: BatchReport
    right: BatchReport
    deltas: Dict[str, Any]

    def summary(self) -> str:
        lines = ["=== Paired Build Comparison ==="]
        for team, delta in sorted(self.deltas.get("win_rate_delta", {}).items()):
            lines.append(f"{team}: win-rate delta {delta * 100:+.1f}%")
        for team, delta in sorted(self.deltas.get("damage_delta", {}).items()):
            lines.append(f"{team}: average damage delta {delta:+.2f}")
        lines.append(f"Average rounds delta: {self.deltas.get('average_rounds_delta', 0.0):+.2f}")
        return "\n".join(lines)
