"""
Avalore Character Simulator - Core Module

This module implements the character mechanics for the Avalore tabletop RPG system.
It includes stats, skills, backgrounds, items, and character persistence.
"""

import json
from typing import Dict, List, Optional, Any
from copy import deepcopy


# Avalore Stat and Skill Definitions
STATS = {
    "Dexterity": ["Acrobatics", "Stealth", "Finesse"],
    "Intelligence": ["Healing", "Perception", "Research"],
    "Harmony": ["Arcana", "Nature", "Belief"],
    "Strength": ["Athletics", "Fortitude", "Forging"]
}

# XP costs for advancement (cost to raise from current level to next level)
# Format: level -> cost to reach next level
XP_COST_STAT = {
    -3: 1, -2: 2, -1: 3, 0: 4, 1: 5, 2: 6
}
XP_COST_SKILL = {
    -3: 1, -2: 1, -1: 2, 0: 2, 1: 3, 2: 3
}

# Stat/Skill limits
STAT_MIN = -3
STAT_MAX = 3
SKILL_MIN = -3
SKILL_MAX = 3


class Item:
    """
    Represents an equippable item in Avalore.
    
    Items can have requirements (stat+skill minimums) and provide modifiers
    to stats, skills, HP, or other attributes.
    """
    
    def __init__(
        self,
        name: str,
        item_type: str,
        requirements: Optional[Dict[str, int]] = None,
        stat_modifiers: Optional[Dict[str, int]] = None,
        skill_modifiers: Optional[Dict[str, Dict[str, int]]] = None,
        hp_modifier: int = 0,
        description: str = ""
    ):
        """
        Initialize an item.
        
        Args:
            name: Item name
            item_type: Type (e.g., "weapon", "armor", "accessory")
            requirements: Dict of "Stat:Skill" -> minimum value
            stat_modifiers: Dict of stat name -> bonus
            skill_modifiers: Dict of stat name -> dict of skill name -> bonus
            hp_modifier: Bonus/penalty to max HP
            description: Item description
        """
        self.name = name
        self.item_type = item_type
        self.requirements = requirements or {}
        self.stat_modifiers = stat_modifiers or {}
        self.skill_modifiers = skill_modifiers or {}
        self.hp_modifier = hp_modifier
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary for serialization."""
        return {
            "name": self.name,
            "item_type": self.item_type,
            "requirements": self.requirements,
            "stat_modifiers": self.stat_modifiers,
            "skill_modifiers": self.skill_modifiers,
            "hp_modifier": self.hp_modifier,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Create item from dictionary."""
        return cls(
            name=data["name"],
            item_type=data["item_type"],
            requirements=data.get("requirements"),
            stat_modifiers=data.get("stat_modifiers"),
            skill_modifiers=data.get("skill_modifiers"),
            hp_modifier=data.get("hp_modifier", 0),
            description=data.get("description", "")
        )


class Character:
    """
    Represents an Avalore character with stats, skills, background, and equipment.
    
    Characters start with all stats and skills at 0 (average human baseline).
    They can be customized through backgrounds, XP spending, and equipment.
    """
    
    def __init__(self, name: str = "Unnamed Character"):
        """
        Initialize a new character.
        
        Args:
            name: Character name
        """
        self.name = name
        
        # Initialize stats and skills to 0 (average human baseline)
        self.base_stats: Dict[str, int] = {
            "Dexterity": 0,
            "Intelligence": 0,
            "Harmony": 0,
            "Strength": 0
        }
        
        self.base_skills: Dict[str, Dict[str, int]] = {
            stat: {skill: 0 for skill in skills}
            for stat, skills in STATS.items()
        }
        
        # Background
        self.background: Optional[str] = None
        
        # Equipment
        self.inventory: List[Item] = []
        self.equipped_items: List[Item] = []
        
        # XP tracking
        self.total_xp: int = 0
        self.spent_xp: int = 0
        
        # Derived stats
        self.base_hp: int = 20  # Base HP for all characters
        self.hp_modifier: int = 0  # From items, feats, etc.
        self.action_count: int = 2  # Default actions per turn
        
        # Current state (for future combat)
        self.current_hp: int = self.get_max_hp()
        
    def get_stat(self, stat_name: str) -> int:
        """
        Get the effective value of a stat (base + modifiers).
        
        Args:
            stat_name: Name of the stat
            
        Returns:
            Total stat value including modifiers
        """
        if stat_name not in self.base_stats:
            raise ValueError(f"Invalid stat: {stat_name}")
        
        value = self.base_stats[stat_name]
        
        # Add modifiers from equipped items
        for item in self.equipped_items:
            if stat_name in item.stat_modifiers:
                value += item.stat_modifiers[stat_name]
        
        return value
    
    def get_skill(self, stat_name: str, skill_name: str) -> int:
        """
        Get the effective value of a skill (base + modifiers).
        
        Args:
            stat_name: Name of the parent stat
            skill_name: Name of the skill
            
        Returns:
            Total skill value including modifiers
        """
        if stat_name not in self.base_skills:
            raise ValueError(f"Invalid stat: {stat_name}")
        if skill_name not in self.base_skills[stat_name]:
            raise ValueError(f"Invalid skill: {skill_name} for stat {stat_name}")
        
        value = self.base_skills[stat_name][skill_name]
        
        # Add modifiers from equipped items
        for item in self.equipped_items:
            if stat_name in item.skill_modifiers:
                if skill_name in item.skill_modifiers[stat_name]:
                    value += item.skill_modifiers[stat_name][skill_name]
        
        return value
    
    def get_modifier(self, stat_name: str, skill_name: str) -> int:
        """
        Get the combined stat+skill modifier for a check.
        
        Args:
            stat_name: Name of the stat
            skill_name: Name of the skill
            
        Returns:
            Sum of stat and skill values (for 2d10 + modifier checks)
        """
        return self.get_stat(stat_name) + self.get_skill(stat_name, skill_name)
    
    def get_max_hp(self) -> int:
        """
        Calculate maximum HP.
        
        Returns:
            Max HP (base + modifiers from items/feats)
        """
        hp = self.base_hp + self.hp_modifier
        
        # Add HP modifiers from equipped items
        for item in self.equipped_items:
            hp += item.hp_modifier
        
        return hp
    
    def get_initiative_modifier(self) -> int:
        """
        Get initiative modifier (based on DEX).
        
        Returns:
            Initiative modifier for determining turn order
        """
        return self.get_stat("Dexterity")
    
    def spend_xp_on_stat(self, stat_name: str, target_level: int) -> bool:
        """
        Spend XP to raise a stat to a target level.
        
        Args:
            stat_name: Name of the stat to raise
            target_level: Desired stat level
            
        Returns:
            True if successful, False if insufficient XP or invalid target
        """
        if stat_name not in self.base_stats:
            raise ValueError(f"Invalid stat: {stat_name}")
        
        current_level = self.base_stats[stat_name]
        
        # Validate target
        if target_level <= current_level:
            return False
        if target_level > STAT_MAX:
            return False
        
        # Calculate XP cost
        total_cost = 0
        for level in range(current_level, target_level):
            if level not in XP_COST_STAT:
                return False
            total_cost += XP_COST_STAT[level]
        
        # Check if enough XP available
        available_xp = self.total_xp - self.spent_xp
        if available_xp < total_cost:
            return False
        
        # Apply the change
        self.base_stats[stat_name] = target_level
        self.spent_xp += total_cost
        return True
    
    def spend_xp_on_skill(self, stat_name: str, skill_name: str, target_level: int) -> bool:
        """
        Spend XP to raise a skill to a target level.
        
        Args:
            stat_name: Name of the parent stat
            skill_name: Name of the skill to raise
            target_level: Desired skill level
            
        Returns:
            True if successful, False if insufficient XP or invalid target
        """
        if stat_name not in self.base_skills:
            raise ValueError(f"Invalid stat: {stat_name}")
        if skill_name not in self.base_skills[stat_name]:
            raise ValueError(f"Invalid skill: {skill_name}")
        
        current_level = self.base_skills[stat_name][skill_name]
        
        # Validate target
        if target_level <= current_level:
            return False
        if target_level > SKILL_MAX:
            return False
        
        # Calculate XP cost
        total_cost = 0
        for level in range(current_level, target_level):
            if level not in XP_COST_SKILL:
                return False
            total_cost += XP_COST_SKILL[level]
        
        # Check if enough XP available
        available_xp = self.total_xp - self.spent_xp
        if available_xp < total_cost:
            return False
        
        # Apply the change
        self.base_skills[stat_name][skill_name] = target_level
        self.spent_xp += total_cost
        return True
    
    def add_xp(self, amount: int):
        """
        Add XP to the character's pool.
        
        Args:
            amount: Amount of XP to add
        """
        self.total_xp += amount
    
    def apply_background(self, background_name: str):
        """
        Apply a background to the character.
        
        Backgrounds provide starting bonuses to stats and skills.
        This should be called during character creation.
        
        Args:
            background_name: Name of the background to apply
        """
        if background_name not in BACKGROUNDS:
            raise ValueError(f"Invalid background: {background_name}")
        
        if self.background is not None:
            raise ValueError("Character already has a background")
        
        background = BACKGROUNDS[background_name]
        self.background = background_name
        
        # Apply stat bonuses
        for stat, bonus in background.get("stat_bonuses", {}).items():
            self.base_stats[stat] += bonus
        
        # Apply skill bonuses
        for stat, skills in background.get("skill_bonuses", {}).items():
            for skill, bonus in skills.items():
                self.base_skills[stat][skill] += bonus
    
    def can_equip_item(self, item: Item) -> bool:
        """
        Check if character meets requirements to equip an item.
        
        Args:
            item: Item to check
            
        Returns:
            True if requirements are met, False otherwise
        """
        for requirement, min_value in item.requirements.items():
            # Parse "Stat:Skill" format
            parts = requirement.split(":")
            if len(parts) != 2:
                continue
            
            stat_name, skill_name = parts
            modifier = self.get_modifier(stat_name, skill_name)
            
            if modifier < min_value:
                return False
        
        return True
    
    def equip_item(self, item: Item) -> bool:
        """
        Equip an item if requirements are met.
        
        Args:
            item: Item to equip
            
        Returns:
            True if successfully equipped, False if requirements not met
        """
        if not self.can_equip_item(item):
            return False
        
        # Add to inventory if not already there
        if item not in self.inventory:
            self.inventory.append(item)
        
        # Equip if not already equipped
        if item not in self.equipped_items:
            self.equipped_items.append(item)
            
            # Update current HP if max HP changed
            old_max = self.get_max_hp()
            new_max = old_max + item.hp_modifier
            if new_max > old_max:
                self.current_hp += (new_max - old_max)
        
        return True
    
    def unequip_item(self, item: Item) -> bool:
        """
        Unequip an item.
        
        Args:
            item: Item to unequip
            
        Returns:
            True if successfully unequipped, False if not equipped
        """
        if item not in self.equipped_items:
            return False
        
        self.equipped_items.remove(item)
        
        # Update current HP if max HP changed
        if item.hp_modifier != 0:
            new_max = self.get_max_hp()
            self.current_hp = min(self.current_hp, new_max)
        
        return True
    
    def get_character_sheet(self) -> str:
        """
        Generate a formatted character sheet.
        
        Returns:
            Multi-line string representation of the character
        """
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"CHARACTER: {self.name}")
        lines.append(f"{'='*60}")
        
        if self.background:
            lines.append(f"Background: {self.background}")
        
        lines.append(f"\nXP: {self.spent_xp}/{self.total_xp} spent")
        lines.append(f"HP: {self.current_hp}/{self.get_max_hp()}")
        lines.append(f"Initiative: +{self.get_initiative_modifier()}")
        lines.append(f"Actions per turn: {self.action_count}")
        
        lines.append(f"\n{'STATS AND SKILLS':-^60}")
        
        for stat_name in ["Dexterity", "Intelligence", "Harmony", "Strength"]:
            stat_value = self.get_stat(stat_name)
            base_value = self.base_stats[stat_name]
            
            if stat_value != base_value:
                lines.append(f"\n{stat_name}: {base_value:+d} (effective: {stat_value:+d})")
            else:
                lines.append(f"\n{stat_name}: {stat_value:+d}")
            
            for skill_name in STATS[stat_name]:
                skill_value = self.get_skill(stat_name, skill_name)
                base_skill = self.base_skills[stat_name][skill_name]
                modifier = self.get_modifier(stat_name, skill_name)
                
                if skill_value != base_skill:
                    lines.append(f"  {skill_name}: {base_skill:+d} (effective: {skill_value:+d}) [total modifier: {modifier:+d}]")
                else:
                    lines.append(f"  {skill_name}: {skill_value:+d} [total modifier: {modifier:+d}]")
        
        if self.equipped_items:
            lines.append(f"\n{'EQUIPPED ITEMS':-^60}")
            for item in self.equipped_items:
                lines.append(f"- {item.name} ({item.item_type})")
                if item.stat_modifiers:
                    lines.append(f"  Stat bonuses: {item.stat_modifiers}")
                if item.skill_modifiers:
                    lines.append(f"  Skill bonuses: {item.skill_modifiers}")
                if item.hp_modifier:
                    lines.append(f"  HP bonus: {item.hp_modifier:+d}")
        
        if self.inventory and len(self.inventory) > len(self.equipped_items):
            lines.append(f"\n{'INVENTORY':-^60}")
            for item in self.inventory:
                if item not in self.equipped_items:
                    lines.append(f"- {item.name} ({item.item_type})")
        
        lines.append(f"{'='*60}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert character to dictionary for serialization.
        
        Returns:
            Dictionary representation of character
        """
        return {
            "name": self.name,
            "base_stats": self.base_stats,
            "base_skills": self.base_skills,
            "background": self.background,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipped_items": [item.name for item in self.equipped_items],
            "total_xp": self.total_xp,
            "spent_xp": self.spent_xp,
            "base_hp": self.base_hp,
            "hp_modifier": self.hp_modifier,
            "action_count": self.action_count,
            "current_hp": self.current_hp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """
        Create character from dictionary.
        
        Args:
            data: Dictionary representation of character
            
        Returns:
            Character instance
        """
        char = cls(name=data["name"])
        char.base_stats = data["base_stats"]
        char.base_skills = data["base_skills"]
        char.background = data.get("background")
        
        # Restore inventory
        char.inventory = [Item.from_dict(item_data) for item_data in data.get("inventory", [])]
        
        # Restore equipped items
        equipped_names = data.get("equipped_items", [])
        char.equipped_items = [item for item in char.inventory if item.name in equipped_names]
        
        char.total_xp = data.get("total_xp", 0)
        char.spent_xp = data.get("spent_xp", 0)
        char.base_hp = data.get("base_hp", 20)
        char.hp_modifier = data.get("hp_modifier", 0)
        char.action_count = data.get("action_count", 2)
        char.current_hp = data.get("current_hp", char.get_max_hp())
        
        return char
    
    def save_to_file(self, filename: str):
        """
        Save character to a JSON file.
        
        Args:
            filename: Path to save file
        """
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'Character':
        """
        Load character from a JSON file.
        
        Args:
            filename: Path to save file
            
        Returns:
            Character instance
        """
        with open(filename, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


# Avalore Backgrounds
# Based on official Avalore rules, backgrounds provide starting bonuses
BACKGROUNDS = {
    "Soldier": {
        "description": "Trained warrior with combat experience",
        "stat_bonuses": {"Strength": 1},
        "skill_bonuses": {}
    },
    "Noble": {
        "description": "High-born with confidence and presence",
        "stat_bonuses": {"Harmony": 1},
        "skill_bonuses": {}
    },
    "Scholar": {
        "description": "Educated and knowledgeable",
        "stat_bonuses": {"Intelligence": 1},
        "skill_bonuses": {}
    },
    "Rogue": {
        "description": "Nimble and stealthy",
        "stat_bonuses": {"Dexterity": 1},
        "skill_bonuses": {}
    },
    "Seafarer": {
        "description": "Sailor or pirate with maritime skills",
        "stat_bonuses": {},
        "skill_bonuses": {"Dexterity": {"Acrobatics": 1}}
    },
    "Warrior": {
        "description": "Battle-hardened fighter",
        "stat_bonuses": {},
        "skill_bonuses": {"Strength": {"Athletics": 1}}
    },
    "Mage": {
        "description": "Trained in arcane arts",
        "stat_bonuses": {},
        "skill_bonuses": {"Harmony": {"Arcana": 1}}
    },
    "Healer": {
        "description": "Skilled in medicine and care",
        "stat_bonuses": {},
        "skill_bonuses": {"Intelligence": {"Healing": 1}}
    },
    "Scout": {
        "description": "Perceptive and aware",
        "stat_bonuses": {},
        "skill_bonuses": {"Intelligence": {"Perception": 1}}
    },
    "Ranger": {
        "description": "Attuned to nature and wilderness",
        "stat_bonuses": {},
        "skill_bonuses": {"Harmony": {"Nature": 1}}
    }
}


# Avalore Items
# Based on official Avalore rules, items have requirements and provide modifiers
ITEMS = {
    "Longbow": Item(
        name="Longbow",
        item_type="weapon",
        requirements={"Dexterity:Acrobatics": 1, "Strength:Athletics": 1},
        description="A powerful ranged weapon requiring dexterity and strength"
    ),
    "Spellblade": Item(
        name="Spellblade",
        item_type="weapon",
        requirements={"Strength:Athletics": 0, "Strength:Fortitude": 1},
        description="A magical weapon balanced for combat"
    ),
    "Heavy Armor": Item(
        name="Heavy Armor",
        item_type="armor",
        requirements={"Strength:Fortitude": 2},
        stat_modifiers={},
        hp_modifier=5,
        description="Heavy armor that protects but requires fortitude"
    ),
    "Belt of Giant Strength": Item(
        name="Belt of Giant Strength",
        item_type="accessory",
        stat_modifiers={"Strength": 1},
        description="A magical belt that enhances strength"
    ),
    "Ring of Intelligence": Item(
        name="Ring of Intelligence",
        item_type="accessory",
        stat_modifiers={"Intelligence": 1},
        description="A magical ring that sharpens the mind"
    ),
    "Thief's Tools": Item(
        name="Thief's Tools",
        item_type="accessory",
        skill_modifiers={"Dexterity": {"Finesse": 1}},
        description="Tools that aid in lockpicking and delicate work"
    ),
    "Cloak of Stealth": Item(
        name="Cloak of Stealth",
        item_type="accessory",
        skill_modifiers={"Dexterity": {"Stealth": 1}},
        description="A cloak that helps the wearer move unseen"
    ),
    "Amulet of Health": Item(
        name="Amulet of Health",
        item_type="accessory",
        hp_modifier=5,
        description="An amulet that bolsters vitality"
    )
}


# Convenience function to create a character with common setup
def create_character(name: str, background: Optional[str] = None, starting_xp: int = 0) -> Character:
    """
    Create a new character with optional background and starting XP.
    
    Args:
        name: Character name
        background: Optional background name
        starting_xp: Starting XP amount
        
    Returns:
        New Character instance
    """
    char = Character(name=name)
    
    if background:
        char.apply_background(background)
    
    if starting_xp > 0:
        char.add_xp(starting_xp)
    
    return char
