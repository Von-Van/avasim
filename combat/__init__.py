# Avalore Combat package

from .engine import AvaCombatEngine
from .participant import CombatParticipant
from .map import TacticalMap, Tile
from .items import Weapon, Armor, Shield, AVALORE_WEAPONS, AVALORE_ARMOR, AVALORE_SHIELDS
from .feats import Feat, AVALORE_FEATS
from .spells import Spell, AVALORE_SPELLS
from .enums import TerrainType, RangeCategory, ArmorCategory, ShieldType, StatusEffect, validate_loadout
from .dice import roll_2d10, roll_1d2, roll_1d3, roll_1d6, set_seed, rng_scope, current_rng
from .feat_handlers import FeatHandler, FeatRegistry, FEAT_REGISTRY
from .ai import CombatAI, STRATEGY_DEFAULTS
from .batch import BatchRunner, BatchConfig, BatchResult
from .events import EventEmitter
from .contracts import (
    BatchReport,
    BatchRequest,
    CharacterBuild,
    ComparisonReport,
    ComparisonRequest,
    ExecutionOptions,
    RunRequest,
    RunResult,
    ScenarioConfig,
    ValidationIssue,
)
from .factory import build_to_participant, builds_to_participants, scenario_to_map
from .runtime import compare, run, run_batch
from .validation import validate_build, validate_run_request, validate_scenario

__all__ = [
    "AvaCombatEngine",
    "CombatParticipant",
    "TacticalMap", "Tile",
    "Weapon", "Armor", "Shield",
    "AVALORE_WEAPONS", "AVALORE_ARMOR", "AVALORE_SHIELDS",
    "Feat", "AVALORE_FEATS",
    "Spell", "AVALORE_SPELLS",
    "TerrainType", "RangeCategory", "ArmorCategory", "ShieldType", "StatusEffect",
    "validate_loadout",
    "roll_2d10", "roll_1d2", "roll_1d3", "roll_1d6", "set_seed", "rng_scope", "current_rng",
    "FeatHandler", "FeatRegistry", "FEAT_REGISTRY",
    "CombatAI", "STRATEGY_DEFAULTS",
    "BatchRunner", "BatchConfig", "BatchResult",
    "EventEmitter",
    "CharacterBuild", "ScenarioConfig", "ExecutionOptions",
    "RunRequest", "RunResult", "BatchRequest", "BatchReport",
    "ComparisonRequest", "ComparisonReport", "ValidationIssue",
    "build_to_participant", "builds_to_participants", "scenario_to_map",
    "run", "run_batch", "compare", "validate_build", "validate_run_request", "validate_scenario",
]
