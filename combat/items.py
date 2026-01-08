from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from .enums import RangeCategory, ArmorCategory, ShieldType
from .dice import roll_1d2, roll_1d3, roll_1d4

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
        from .dice import roll_1d4
        if self.category == ArmorCategory.LIGHT:
            soak = max(0, roll_1d2() - 1)  # 1d2-1 (0 or 1)
        elif self.category == ArmorCategory.MEDIUM:
            soak = max(0, roll_1d3() - 1)  # 1d3-1 (0 to 2)
        elif self.category == ArmorCategory.HEAVY:
            soak = roll_1d3()  # 1d3 (1 to 3)
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
    # Melee Weapons
    "Unarmed": Weapon(name="Unarmed", damage=1, accuracy_bonus=2, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, description="Fists and natural weapons. +2 to hit, base 1 damage (scales with STR:Athletics: +1 dmg at +1, +2 at +3, +3 at +5)."),
    "Arming Sword": Weapon(name="Arming Sword", damage=4, accuracy_bonus=1, range_category=RangeCategory.MELEE, is_two_handed=False, stat_requirements={"Strength:Athletics": 0}, description="A well-balanced one-handed sword. +1 to hit, 4 damage, 1 action."),
    "Polearm": Weapon(name="Polearm", damage=6, accuracy_bonus=2, actions_required=2, range_category=RangeCategory.MELEE, is_two_handed=True, reach=2, armor_piercing=True, stat_requirements={"Strength:Athletics": 2, "Dexterity:Acrobatics": 2}, traits=["piercing", "reach"], description="Two-handed reach weapon; +2 to hit, 6 damage, 2 actions (Lift/Strike), pierces armor."),
    "Mace": Weapon(name="Mace", damage=3, accuracy_bonus=1, range_category=RangeCategory.MELEE, is_two_handed=False, stat_requirements={"Dexterity:Acrobatics": -1}, traits=["vs_medium_heavy_bonus"], description="A heavy blunt weapon. +1 to hit, 3 damage (+2 vs medium/heavy armor), 1 action."),
    "Large Shield": Weapon(name="Large Shield", damage=2, accuracy_bonus=0, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, armor_piercing=True, stat_requirements={"Strength:Athletics": 2, "Strength:Fortitude": 2}, traits=["piercing"], description="Large shield bash. +0 to hit, 2 damage, 1 action, pierces armor."),
    "Staff": Weapon(name="Staff", damage=5, accuracy_bonus=2, actions_required=2, range_category=RangeCategory.MELEE, is_two_handed=True, stat_requirements={"Dexterity:Acrobatics": 2}, traits=["grazing"], description="A quarterstaff. +2 to hit, 5 damage, 2 actions (Lift & Strike), bypasses grazing."),
    "Small Weapon": Weapon(name="Small Weapon", damage=3, accuracy_bonus=3, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, is_small_weapon=True, stat_requirements={"Dexterity:Acrobatics": -1}, description="Daggers, short swords. +3 to hit, 3 damage, 1 action. Can carry one extra for free."),
    "Greatsword": Weapon(name="Greatsword", damage=8, accuracy_bonus=1, actions_required=2, range_category=RangeCategory.MELEE, is_two_handed=True, stat_requirements={"Strength:Athletics": 2}, description="A massive two-handed sword. +1 to hit, 8 damage, 2 actions (Lift/Strike)."),
    "Finesse Blade": Weapon(name="Finesse Blade", damage=3, accuracy_bonus=3, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, stat_requirements={"Dexterity:Finesse": 2}, traits=["vs_unarmored_bonus", "grazing"], description="Rapiers, scimitars. +3 to hit, 3 damage (+1 vs unarmored), 1 action, bypasses grazing."),
    "Small Shield": Weapon(name="Small Shield", damage=3, accuracy_bonus=1, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, armor_piercing=True, stat_requirements={"Strength:Athletics": 0, "Strength:Fortitude": 1}, traits=["piercing", "grazing"], description="Buckler bash. +1 to hit, 3 damage, 1 action, pierces armor and bypasses grazing."),
    "Spellblade": Weapon(name="Spellblade", damage=4, accuracy_bonus=1, actions_required=1, range_category=RangeCategory.MELEE, is_two_handed=False, stat_requirements={"Harmony:Arcana": 2, "Strength:Athletics": 0}, description="A magically-infused blade. +1 to hit, 4 damage, 1 action."),
    
    # Skirmishing Weapons (2-8 blocks)
    "Javelin": Weapon(name="Javelin", damage=5, accuracy_bonus=1, actions_required=2, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, armor_piercing=True, usable_underwater=True, stat_requirements={"Dexterity:Acrobatics": 1, "Strength:Athletics": 1}, traits=["piercing"], description="A throwing spear. +1 to hit, 5 damage, 2 actions (Lift/Throw), pierces armor, works underwater."),
    "Sling": Weapon(name="Sling", damage=6, accuracy_bonus=1, actions_required=2, range_category=RangeCategory.SKIRMISHING, is_two_handed=True, load_time=1, stat_requirements={"Dexterity:Acrobatics": 1}, description="A sling for hurling stones. +1 to hit, 6 damage, 2 actions (load & loose)."),
    "Throwing Knife": Weapon(name="Throwing Knife", damage=4, accuracy_bonus=1, actions_required=1, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, stat_requirements={"Dexterity:Acrobatics": 0}, traits=["hidden_on_miss"], description="Throwing weapon. +1 to hit, 4 damage, 1 action. Does not reveal Hidden thrower on miss."),
    "Meteor Hammer": Weapon(name="Meteor Hammer", damage=3, accuracy_bonus=2, actions_required=1, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, is_small_weapon=True, stat_requirements={"Dexterity:Acrobatics": 1}, traits=["vs_medium_heavy_bonus"], description="A chain weapon. +2 to hit, 3 damage (+1 vs medium/heavy armor), 1 action."),
    "Whip": Weapon(name="Whip", damage=3, accuracy_bonus=3, actions_required=1, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, stat_requirements={"Dexterity:Finesse": 1}, traits=["vs_unarmored_bonus", "grazing", "no_heavy_armor_damage"], description="A flexible whip. +3 to hit, 3 damage (+1 vs unarmored), 1 action, bypasses grazing. Cannot penetrate heavy armor."),
    "Arcane Wand": Weapon(name="Arcane Wand", damage=2, accuracy_bonus=2, actions_required=1, range_category=RangeCategory.SKIRMISHING, is_two_handed=False, armor_piercing=True, stat_requirements={"Harmony:Arcana": 2}, traits=["piercing"], usable_underwater=True, description="A magical wand. +2 to hit, 2 damage, 1 action, pierces armor, works underwater."),
    
    # Ranged Weapons (6-30 blocks)
    "Recurve Bow": Weapon(name="Recurve Bow", damage=3, accuracy_bonus=2, actions_required=1, range_category=RangeCategory.RANGED, is_two_handed=True, stat_requirements={"Dexterity:Finesse": 1}, usable_underwater=False, traits=["vs_unarmored_bonus", "grazing"], description="A lighter bow. +2 to hit, 3 damage (+1 vs unarmored), 1 action, bypasses grazing. Cannot be used in heavy armor."),
    "Crossbow": Weapon(name="Crossbow", damage=5, accuracy_bonus=3, actions_required=2, range_category=RangeCategory.RANGED, is_two_handed=True, armor_piercing=True, load_time=1, stat_requirements={"Strength:Athletics": 1}, usable_underwater=True, traits=["piercing"], description="A crossbow with AP. +3 to hit, 5 damage, 2 actions (load & fire), pierces armor, works underwater."),
    "Longbow": Weapon(name="Longbow", damage=6, accuracy_bonus=3, actions_required=2, range_category=RangeCategory.RANGED, is_two_handed=True, draw_time=1, stat_requirements={"Dexterity:Acrobatics": 1, "Strength:Athletics": 1}, usable_underwater=False, description="A powerful longbow. +3 to hit, 6 damage, 2 actions (nock & loose). Cannot be used in heavy armor or underwater."),
    "Spellbook": Weapon(name="Spellbook", damage=4, accuracy_bonus=3, actions_required=2, range_category=RangeCategory.RANGED, is_two_handed=True, armor_piercing=True, stat_requirements={"Harmony:Arcana": 2}, traits=["piercing"], usable_underwater=True, description="Arcane tome for casting. +3 to hit, 4 damage, 2 actions (chant & cast), pierces armor, works underwater."),
}

AVALORE_ARMOR = {
    "Light Armor": Armor(name="Light Armor", category=ArmorCategory.LIGHT, evasion_penalty=0, stealth_penalty=0, movement_penalty=0, stat_requirements={"Dexterity:Acrobatics": -1}, description="Leather or padded armor. 1d2-1 protection (0-1 soak), no penalties."),
    "Medium Armor": Armor(name="Medium Armor", category=ArmorCategory.MEDIUM, evasion_penalty=-1, stealth_penalty=0, movement_penalty=0, stat_requirements={"Strength:Athletics": 1}, description="Chain, scale, breastplate. 1d4-1 protection (0-3 soak), -1 evasion. If not meeting requirement: -2 movement, -1 additional soak penalty."),
    "Heavy Armor": Armor(name="Heavy Armor", category=ArmorCategory.HEAVY, evasion_penalty=-2, stealth_penalty=-3, movement_penalty=-2, stat_requirements={"Strength:Athletics": 3}, description="Full plate. 1d4 protection (1-4 soak), -2 evasion, -3 stealth, -2 movement. If not meeting requirement: -2 additional movement, -1 additional soak penalty."),
}

AVALORE_SHIELDS = {
    "Small Shield": Shield(name="Small Shield", shield_type=ShieldType.SMALL, block_modifier=-3, grants_ap_immunity=False, stat_requirements={"Dexterity:Finesse": 2, "Strength:Athletics": 2}, description="A buckler. 2d10-3 to block, requires DEX:Finesse 2 and STR:Athletics 2."),
    "Large Shield": Shield(name="Large Shield", shield_type=ShieldType.LARGE, block_modifier=-2, grants_ap_immunity=True, stat_requirements={"Strength:Athletics": 2, "Strength:Fortitude": 2}, description="A tower shield. 2d10-2 to block, grants AP immunity, requires STR:Athletics 2 and STR:Fortitude 2."),
}
