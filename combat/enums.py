from enum import Enum, auto
from typing import List

class TerrainType(Enum):
    NORMAL = "normal"
    FOREST = "forest"
    WATER = "water"
    MOUNTAIN = "mountain"
    ROAD = "road"
    WALL = "wall"

class RangeCategory(Enum):
    MELEE = "melee"
    SKIRMISHING = "skirmishing"
    RANGED = "ranged"

class ArmorCategory(Enum):
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"

class ShieldType(Enum):
    SMALL = "small"
    LARGE = "large"

class StatusEffect(Enum):
    PRONE = auto()
    SLOWED = auto()
    DISARMED = auto()
    MARKED = auto()
    VULNERABLE = auto()
    HIDDEN = auto()

MAX_WEAPONS = 2
MAX_SMALL_FLEX = 1

def validate_loadout(weapons: List[str]) -> bool:
    small_flex = {"Throwing Knife", "Whip", "Dagger", "Meteor Hammer"}
    big = sum(1 for w in weapons if w not in small_flex)
    small = sum(1 for w in weapons if w in small_flex)
    return big <= MAX_WEAPONS and small <= MAX_SMALL_FLEX
