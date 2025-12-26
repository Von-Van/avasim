"""
Avalore Character Simulator

A comprehensive Python-based simulator for the Avalore tabletop RPG system,
including character creation, management, and full combat mechanics.
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

try:
    from .combat import (
        Weapon,
        Armor,
        Shield,
        Feat,
        Spell,
        CombatParticipant,
        AvaCombatEngine,
        AVALORE_WEAPONS,
        AVALORE_ARMOR,
        AVALORE_SHIELDS,
        AVALORE_FEATS,
        AVALORE_SPELLS,
        RangeCategory,
        ArmorCategory,
        ShieldType,
        roll_2d10,
        roll_1d2,
        roll_1d3,
        roll_1d6,
    )
    _combat_available = True
except Exception:
    _combat_available = False

__version__ = "2.0.0"
__all__ = [
    # Character system
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
    "SKILL_MAX",
]

# Add combat exports if available
if _combat_available:
    __all__ += [
        # Combat classes
        "Weapon",
        "Armor",
        "Shield",
        "Feat",
        "Spell",
        "CombatParticipant",
        "AvaCombatEngine",
        # Combat databases
        "AVALORE_WEAPONS",
        "AVALORE_ARMOR",
        "AVALORE_SHIELDS",
        "AVALORE_FEATS",
        "AVALORE_SPELLS",
        # Enums
        "RangeCategory",
        "ArmorCategory",
        "ShieldType",
        # Dice utilities
        "roll_2d10",
        "roll_1d2",
        "roll_1d3",
        "roll_1d6",
    ]
