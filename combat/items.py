from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from .enums import RangeCategory, ArmorCategory, ShieldType
from .dice import roll_1d2, roll_1d3

@dataclass
class Weapon:
    name: str
    damage: int
    accuracy_bonus: int = 0
    actions_required: int = 1
    range_category: RangeCategory = RangeCategory.MELEE
    is_two_handed: bool = False
    armor_piercing: bool = False
    stat_requirements: Dict[str, int] = field(default_factory=dict)
    usable_underwater: bool = True
    is_small_weapon: bool = False
    reach: int = 1
    load_time: int = 0
    draw_time: int = 0
    traits: List[str] = field(default_factory=list)
    description: str = ""

    def meets_requirements(self, character) -> bool:
        for req, min_val in self.stat_requirements.items():
            parts = req.split(":")
            if len(parts) == 2:
                stat, skill = parts
                if character.get_modifier(stat, skill) < min_val:
                    return False
        return True

    def is_piercing(self) -> bool:
        return self.armor_piercing or ("piercing" in self.traits)

@dataclass
class Armor:
    name: str
    category: ArmorCategory = ArmorCategory.NONE
    evasion_penalty: int = 0
    stealth_penalty: int = 0
    movement_penalty: int = 0
    stat_requirements: Dict[str, int] = field(default_factory=dict)
    description: str = ""

    def get_soak_value(self, meets_requirement: bool = True) -> int:
        if self.category == ArmorCategory.LIGHT:
            soak = max(0, roll_1d2() - 1)
        elif self.category == ArmorCategory.MEDIUM:
            soak = max(0, roll_1d3() - 1)
        elif self.category == ArmorCategory.HEAVY:
            soak = roll_1d3()
        else:
            soak = 0
        if not meets_requirement:
            soak = max(0, soak - 1)
        return soak

    def prohibits_weapon(self, weapon: Weapon) -> bool:
        if self.category == ArmorCategory.HEAVY:
            if "Longbow" in weapon.name or "Recurve" in weapon.name:
                return True
        return False

    def meets_requirements(self, character) -> bool:
        for req, min_val in self.stat_requirements.items():
            parts = req.split(":")
            if len(parts) == 2:
                stat, skill = parts
                if character.get_modifier(stat, skill) < min_val:
                    return False
        return True

    def movement_penalty_for(self, character) -> int:
        base = self.movement_penalty
        if not self.meets_requirements(character):
            base -= 2
        return base

@dataclass
class Shield:
    name: str
    shield_type: ShieldType = ShieldType.SMALL
    block_modifier: int = -3
    grants_ap_immunity: bool = False
    ranged_bonus: int = 1
    stat_requirements: Dict[str, int] = field(default_factory=dict)
    description: str = ""

    def get_block_dc(self) -> int:
        return 12

    def roll_block(self, is_ranged_attack: bool = False, extra_bonus: int = 0) -> Tuple[int, bool]:
        from .dice import roll_2d10
        total, _ = roll_2d10()
        bonus = self.ranged_bonus if is_ranged_attack else 0
        final_roll = total + self.block_modifier + bonus + extra_bonus
        success = final_roll >= 12
        return final_roll, success

    def meets_requirements(self, character) -> bool:
        for req, min_val in self.stat_requirements.items():
            parts = req.split(":")
            if len(parts) == 2:
                stat, skill = parts
                if character.get_modifier(stat, skill) < min_val:
                    return False
        return True

# Predefined items
AVALORE_WEAPONS: Dict[str, Weapon] = {
    "Dagger": Weapon(name="Dagger", damage=3, accuracy_bonus=3, range_category=RangeCategory.MELEE, is_two_handed=False, is_small_weapon=True, stat_requirements={"Dexterity:Acrobatics": -1}, description="A small blade, easily concealed. +3 to hit, 3 damage. Can be dual-wielded."),
    "Arming Sword": Weapon(name="Arming Sword", damage=4, accuracy_bonus=1, range_category=RangeCategory.MELEE, is_two_handed=False, description="A well-balanced one-handed sword. +1 to hit, 4 damage."),
    "Rapier": Weapon(name="Rapier", damage=3, accuracy_bonus=3, range_category=RangeCategory.MELEE, is_two_handed=False, stat_requirements={"Dexterity:Finesse": 2}, traits=["grazing", "vs_unarmored_bonus"], description="A thin, precise blade; +3 to hit, bypasses grazing, +1 damage vs unarmored."),
    "Mace": Weapon(name="Mace", damage=3, accuracy_bonus=1, range_category=RangeCategory.MELEE, is_two_handed=False, traits=["vs_medium_heavy_bonus"], description="A heavy blunt weapon. +2 dmg vs medium/heavy armor."),
    "Greatsword": Weapon(name="Greatsword", damage=8, accuracy_bonus=1, actions_required=2, range_category=RangeCategory.MELEE, is_two_handed=True, stat_requirements={"Strength:Athletics": 2}, description="A massive two-handed sword. +1 to hit, 8 damage, requires 2 actions (Lift/Strike)."),
    "Greataxe": Weapon(name="Greataxe", damage=8, accuracy_bonus=0, actions_required=2, range_category=RangeCategory.MELEE, is_two_handed=True, stat_requirements={"Strength:Athletics": 2}, traits=["cleave"], description="Heavy two-handed axe; brutal swings, 2 actions."),
    "Spear": Weapon(name="Spear", damage=6, accuracy_bonus=2, actions_required=2, range_category=RangeCategory.SKIRMISHING, is_two_handed=True, reach=2, traits=["piercing", "reach"], description="A polearm with reach; 2 actions (lift/strike)."),
    "Polearm": Weapon(name="Polearm", damage=6, accuracy_bonus=2, actions_required=2, range_category=RangeCategory.SKIRMISHING, is_two_handed=True, reach=2, traits=["piercing", "reach"], description="Two-handed reach weapon; +2 to hit, 6 damage, 2 actions (Lift/Strike), pierces armor."),
    "Javelin": Weapon(name="Javelin", damage=5, accuracy_bonus=1, actions_required=2, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, usable_underwater=True, traits=["piercing"], stat_requirements={"Dexterity:Acrobatics": 1, "Strength:Athletics": 1}, description="A throwing spear, works underwater. 5 damage, 2 actions."),
    "Sling": Weapon(name="Sling", damage=6, accuracy_bonus=1, actions_required=2, range_category=RangeCategory.SKIRMISHING, is_two_handed=True, load_time=1, stat_requirements={"Dexterity:Acrobatics": 1}, description="A sling for hurling stones. +1 to hit, 6 damage, 2 actions (1 to load), requires DEX:Acrobatics +1."),
    "Longbow": Weapon(name="Longbow", damage=6, accuracy_bonus=3, actions_required=2, range_category=RangeCategory.RANGED, is_two_handed=True, draw_time=1, stat_requirements={"Strength:Athletics": 1, "Dexterity:Acrobatics": 1}, usable_underwater=False, description="A powerful longbow. +3 to hit, 6 damage, 2 actions (1 action to draw). Cannot be used in heavy armor or underwater."),
    "Recurve Bow": Weapon(name="Recurve Bow", damage=3, accuracy_bonus=2, actions_required=1, range_category=RangeCategory.RANGED, is_two_handed=True, stat_requirements={"Dexterity:Finesse": 1}, usable_underwater=False, traits=["vs_unarmored_bonus", "grazing"], description="A lighter bow. +2 to hit, 3 damage (+1 vs unarmored), 1 action. Cannot be used in heavy armor."),
    "Crossbow": Weapon(name="Crossbow", damage=5, accuracy_bonus=3, actions_required=2, range_category=RangeCategory.RANGED, is_two_handed=True, armor_piercing=True, load_time=1, traits=["piercing"], stat_requirements={"Strength:Athletics": 1}, usable_underwater=True, description="A crossbow with AP. Works underwater. +3 to hit, 5 damage, 2 actions (1 action to reload)."),
    "Unarmed": Weapon(name="Unarmed", damage=2, accuracy_bonus=2, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, description="Fists and natural weapons. +2 to hit, damage scales with STR:Athletics."),
    "Staff": Weapon(name="Staff", damage=5, accuracy_bonus=2, actions_required=2, range_category=RangeCategory.MELEE, is_two_handed=False, stat_requirements={"Dexterity:Acrobatics": 2}, traits=["grazing"], description="A quarterstaff. +2 to hit, 5 damage, 2 actions (Lift & Strike), bypasses grazing."),
    "Whip": Weapon(name="Whip", damage=3, accuracy_bonus=3, actions_required=1, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, stat_requirements={"Dexterity:Finesse": 1}, traits=["vs_unarmored_bonus", "grazing", "no_heavy_armor_damage"], description="A flexible whip. +3 to hit, 3 damage (+1 vs unarmored), 1 action. Cannot penetrate heavy armor."),
    "Meteor Hammer": Weapon(name="Meteor Hammer", damage=3, accuracy_bonus=2, actions_required=1, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, is_small_weapon=True, stat_requirements={"Dexterity:Acrobatics": 1}, traits=["vs_medium_heavy_bonus"], description="A chain weapon. +2 to hit, 3 damage (+1 vs medium/heavy armor), 1 action."),
    "Throwing Knife": Weapon(name="Throwing Knife", damage=4, accuracy_bonus=1, actions_required=1, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, stat_requirements={"Dexterity:Acrobatics": 0}, traits=["hidden_on_miss"], description="A throwing weapon. +1 to hit, 4 damage, 1 action. Does not reveal Hidden thrower on miss."),
    "Small Shield": Weapon(name="Small Shield", damage=3, accuracy_bonus=1, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, armor_piercing=True, stat_requirements={"Strength:Athletics": 0, "Strength:Fortitude": 1}, traits=["piercing", "grazing"], description="Shield bash. +1 to hit, 3 damage, 1 action. Pierces armor and bypasses grazing."),
    "Large Shield": Weapon(name="Large Shield", damage=2, accuracy_bonus=0, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, armor_piercing=True, stat_requirements={"Strength:Athletics": 2, "Strength:Fortitude": 2}, traits=["piercing"], description="Large shield bash. +0 to hit, 2 damage, 1 action. Pierces armor."),
    "Spellblade": Weapon(name="Spellblade", damage=4, accuracy_bonus=1, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, stat_requirements={"Harmony:Arcana": 2, "Strength:Athletics": 0}, description="A magically-infused blade. +1 to hit, 4 damage, 1 action."),
    "Arcane Wand": Weapon(name="Arcane Wand", damage=2, accuracy_bonus=2, actions_required=1, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, armor_piercing=True, stat_requirements={"Harmony:Arcana": 2}, traits=["piercing"], usable_underwater=True, description="A magical wand. +2 to hit, 2 damage, 1 action. Pierces armor, works underwater."),
    "Spellbook": Weapon(name="Spellbook", damage=4, accuracy_bonus=3, actions_required=2, range_category=RangeCategory.RANGED, is_two_handed=True, armor_piercing=True, stat_requirements={"Harmony:Arcana": 2}, traits=["piercing"], usable_underwater=True, description="Arcane tome for casting. +3 to hit, 4 damage, 2 actions. Pierces armor, works underwater."),
}

AVALORE_ARMOR = {
    "Light Armor": Armor(name="Light Armor", category=ArmorCategory.LIGHT, evasion_penalty=0, stealth_penalty=0, movement_penalty=0, stat_requirements={"Dexterity:Acrobatics": -1}, description="Leather or padded armor. 1d2-1 protection, no penalties."),
    "Medium Armor": Armor(name="Medium Armor", category=ArmorCategory.MEDIUM, evasion_penalty=-1, stealth_penalty=0, movement_penalty=0, stat_requirements={"Strength:Athletics": 1}, description="Breastplate or half-plate. 1d3-1 protection, -1 evasion."),
    "Heavy Armor": Armor(name="Heavy Armor", category=ArmorCategory.HEAVY, evasion_penalty=-2, stealth_penalty=-3, movement_penalty=-1, stat_requirements={"Strength:Athletics": 3}, description="Full plate. 1d3 protection, -2 evasion, -3 stealth, -1 movement."),
}

AVALORE_SHIELDS = {
    "Small Shield": Shield(name="Small Shield", shield_type=ShieldType.SMALL, block_modifier=-3, grants_ap_immunity=False, stat_requirements={"Dexterity:Finesse": 2, "Strength:Athletics": 2}, description="A buckler. 2d10-3 to block, requires DEX:Finesse 2 and STR:Athletics 2."),
    "Large Shield": Shield(name="Large Shield", shield_type=ShieldType.LARGE, block_modifier=-2, grants_ap_immunity=True, stat_requirements={"Strength:Athletics": 2, "Strength:Fortitude": 2}, description="A tower shield. 2d10-2 to block, grants AP immunity, requires STR:Athletics 2 and STR:Fortitude 2."),
}
