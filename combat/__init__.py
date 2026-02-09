# Avalore Combat package

from .engine import AvaCombatEngine
from .participant import CombatParticipant
from .map import TacticalMap, Tile
from .items import Weapon, Armor, Shield, AVALORE_WEAPONS, AVALORE_ARMOR, AVALORE_SHIELDS
from .feats import Feat, AVALORE_FEATS
from .spells import Spell, AVALORE_SPELLS
from .enums import TerrainType, RangeCategory, ArmorCategory, ShieldType, StatusEffect, validate_loadout
from .dice import roll_2d10, roll_1d2, roll_1d3, roll_1d6
from .feat_handlers import FeatHandler, FeatRegistry, FEAT_REGISTRY

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
    "roll_2d10", "roll_1d2", "roll_1d3", "roll_1d6",
    "FeatHandler", "FeatRegistry", "FEAT_REGISTRY",
]