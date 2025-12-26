from dataclasses import dataclass, field
from typing import Dict
from .enums import RangeCategory

@dataclass
class Spell:
    name: str
    discipline: str
    anima_cost: int
    actions_required: int = 1
    casting_dc: int = 10
    damage: int = 0
    healing: int = 0
    range_category: RangeCategory = RangeCategory.RANGED
    requires_attack_roll: bool = False
    description: str = ""

    def can_cast(self, character) -> bool:
        return character.anima >= self.anima_cost

AVALORE_SPELLS: Dict[str, Spell] = {
    "Force Bolt": Spell(name="Force Bolt", discipline="Force", anima_cost=1, actions_required=1, damage=4, range_category=RangeCategory.RANGED, requires_attack_roll=False, description="A bolt of force energy. Auto-hits on successful cast. 4 damage."),
    "Healing Touch": Spell(name="Healing Touch", discipline="Ichor", anima_cost=2, actions_required=1, healing=5, range_category=RangeCategory.MELEE, description="Restore 5 HP to target."),
    "Firebolt": Spell(name="Firebolt", discipline="Force", anima_cost=2, actions_required=1, damage=6, range_category=RangeCategory.RANGED, requires_attack_roll=False, description="A bolt of fire. 6 fire damage on successful cast."),
}
