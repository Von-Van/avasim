"""
Avalore Character Simulator

A Python-based character simulator for the Avalore tabletop RPG system.
"""

from .avasim import (
    Character,
    Item,
    STATS,
    BACKGROUNDS,
    ITEMS,
    create_character,
    XP_COST_STAT,
    XP_COST_SKILL,
    STAT_MIN,
    STAT_MAX,
    SKILL_MIN,
    SKILL_MAX
)

__version__ = "1.0.0"
__all__ = [
    "Character",
    "Item",
    "STATS",
    "BACKGROUNDS",
    "ITEMS",
    "create_character",
    "XP_COST_STAT",
    "XP_COST_SKILL",
    "STAT_MIN",
    "STAT_MAX",
    "SKILL_MIN",
    "SKILL_MAX"
]
