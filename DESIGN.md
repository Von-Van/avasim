# Avalore Character Simulator - Design Documentation

## Overview

This document describes the architecture and design decisions for the Avalore character simulator, focusing on how the current implementation supports future expansion to include full combat mechanics.

## Architecture

### Core Classes

#### Character Class
The `Character` class is the central component that manages all character state:

```python
Character(name: str)
```

**Key Attributes:**
- `base_stats`: Dictionary of stat names to base values
- `base_skills`: Nested dictionary of stats -> skills -> values
- `background`: Character's background (applied once)
- `inventory`: List of all items the character owns
- `equipped_items`: List of currently equipped items
- `total_xp` / `spent_xp`: Experience point tracking
- `base_hp` / `hp_modifier`: Health point management
- `current_hp`: Current health (for combat)
- `action_count`: Actions per turn (default 2)

**Key Methods:**
- `get_stat(stat_name)`: Returns effective stat value (base + modifiers)
- `get_skill(stat_name, skill_name)`: Returns effective skill value
- `get_modifier(stat_name, skill_name)`: Returns combined stat+skill for checks
- `spend_xp_on_stat()` / `spend_xp_on_skill()`: Character advancement
- `equip_item()` / `unequip_item()`: Equipment management
- `save_to_file()` / `load_from_file()`: Persistence

#### Item Class
The `Item` class represents equipment with requirements and modifiers:

```python
Item(name, item_type, requirements, stat_modifiers, skill_modifiers, hp_modifier, description)
```

**Key Features:**
- Stat/skill requirements (e.g., "Dexterity:Acrobatics": 1)
- Modifiers to stats, skills, or HP
- Serialization support for persistence

### Data Structures

#### Stats and Skills
The game uses a two-level hierarchy:

```python
STATS = {
    "Dexterity": ["Acrobatics", "Stealth", "Finesse"],
    "Intelligence": ["Healing", "Perception", "Research"],
    "Harmony": ["Arcana", "Nature", "Belief"],
    "Strength": ["Athletics", "Fortitude", "Forging"]
}
```

#### Backgrounds
Backgrounds are defined in a dictionary:

```python
BACKGROUNDS = {
    "Background Name": {
        "description": "...",
        "stat_bonuses": {"Stat": value},
        "skill_bonuses": {"Stat": {"Skill": value}}
    }
}
```

#### Items
Items are pre-defined in the `ITEMS` dictionary for easy access.

## Design Principles

### 1. Separation of Base and Effective Values
The system maintains separate base values and effective values:
- Base values are permanent (from backgrounds, XP spending)
- Effective values include temporary modifiers (from equipment)
- This makes it easy to equip/unequip items without losing base stats

### 2. Modular Stat Calculation
All stat/skill calculations go through getter methods:
- `get_stat()` computes: base + item bonuses
- `get_skill()` computes: base + item bonuses
- `get_modifier()` computes: stat + skill (for 2d10 + modifier checks)

This centralization makes it easy to add new modifier sources (feats, buffs, etc.)

### 3. Requirement Checking
Items can have requirements in "Stat:Skill" format:
```python
requirements = {"Dexterity:Acrobatics": 1, "Strength:Athletics": 1}
```

The `can_equip_item()` method parses these and checks combined modifiers.

### 4. JSON Persistence
Characters serialize to human-readable JSON:
- All state is captured (stats, skills, items, XP)
- Items are stored with full definitions
- Equipped items tracked separately by name

## Future Expansion: Combat Module

The current design supports future combat expansion through:

### 1. Initiative System
Already implemented:
```python
char.get_initiative_modifier()  # Returns DEX for initiative rolls
```

Combat module can use: `2d10 + get_initiative_modifier()` for turn order.

### 2. Action Economy
Already tracked:
```python
char.action_count  # Default 2, modifiable by feats
```

Combat module can decrement this each turn and reset at turn start.

### 3. Health Management
Already implemented:
```python
char.current_hp  # Tracks damage
char.get_max_hp()  # Computes max including modifiers
```

Combat module can:
- Subtract damage from `current_hp`
- Check for unconsciousness (current_hp <= 0)
- Implement healing

### 4. Attack/Defense Rolls
The modifier system supports combat:
```python
# Attack roll
attack_roll = 2d10 + char.get_modifier("Strength", "Athletics")

# Dodge roll
dodge_roll = 2d10 + char.get_modifier("Dexterity", "Acrobatics")
```

### 5. Placeholder Methods
Consider adding placeholder methods for future implementation:

```python
class Character:
    def attack(self, target, weapon=None):
        """Placeholder for combat attack action."""
        pass
    
    def cast_spell(self, spell, target=None):
        """Placeholder for spellcasting."""
        pass
    
    def move(self, distance):
        """Placeholder for tactical movement."""
        pass
```

### 6. Combat State
Future additions might include:
```python
# Position tracking (for tactical grid)
self.position = (x, y)

# Status effects
self.status_effects = []  # ["stunned", "poisoned", etc.]

# Temporary buffs/debuffs
self.temp_stat_modifiers = {}
self.temp_skill_modifiers = {}

# Resource tracking (Anima for spells)
self.anima = 0
self.max_anima = 0
```

## Extensibility Points

### Adding New Backgrounds
Add to `BACKGROUNDS` dictionary:
```python
BACKGROUNDS["Merchant"] = {
    "description": "Skilled trader",
    "stat_bonuses": {"Intelligence": 1},
    "skill_bonuses": {}
}
```

### Adding New Items
Add to `ITEMS` dictionary:
```python
ITEMS["Magic Staff"] = Item(
    name="Magic Staff",
    item_type="weapon",
    requirements={"Harmony:Arcana": 2},
    stat_modifiers={"Harmony": 1}
)
```

### Adding Feats (Future)
Create a `Feat` class similar to `Item`:
```python
class Feat:
    def __init__(self, name, requirements, effects):
        self.name = name
        self.requirements = requirements  # Stat/skill minimums
        self.effects = effects  # Passive bonuses, special abilities
```

Add to `Character`:
```python
self.feats = []  # List of acquired feats

def add_feat(self, feat):
    # Check prerequisites
    # Add to character
    # Apply passive effects
```

### Adding Spells (Future)
Create a `Spell` class:
```python
class Spell:
    def __init__(self, name, anima_cost, casting_stat, casting_skill):
        self.name = name
        self.anima_cost = anima_cost
        self.casting_stat = casting_stat  # e.g., "Harmony"
        self.casting_skill = casting_skill  # e.g., "Arcana"
```

### Adding Combat (Future)
Create a `Combat` class:
```python
class Combat:
    def __init__(self, participants):
        self.participants = participants
        self.turn_order = []
        self.current_turn = 0
    
    def roll_initiative(self):
        # Roll 2d10 + DEX for each participant
        # Sort by result
        pass
    
    def next_turn(self):
        # Advance to next character
        # Reset action counts
        pass
```

## XP Costs

Current cost structure (can be adjusted):

**Stats:**
- -3 to -2: 1 XP
- -2 to -1: 2 XP
- -1 to 0: 3 XP
- 0 to 1: 4 XP
- 1 to 2: 5 XP
- 2 to 3: 6 XP

**Skills:**
- -3 to -2: 1 XP
- -2 to -1: 1 XP
- -1 to 0: 2 XP
- 0 to 1: 2 XP
- 1 to 2: 3 XP
- 2 to 3: 3 XP

Total cost from 0 to 3:
- Stat: 4 + 5 + 6 = 15 XP
- Skill: 2 + 2 + 3 = 7 XP

## Testing Strategy

Current test coverage includes:
- Character creation and defaults
- Stat/skill system with modifiers
- Background application
- XP spending and limits
- Item requirements and modifiers
- Persistence (save/load)
- Integration scenarios

When adding new features:
1. Add unit tests for the feature
2. Add integration tests showing feature interaction
3. Update examples to demonstrate usage
4. Update documentation

## Performance Considerations

Current implementation prioritizes clarity over performance, suitable for:
- Single character management
- Turn-based gameplay
- Local file storage

For future scaling:
- Consider caching effective stat values
- Batch stat calculations if managing many NPCs
- Use database for large character collections

## Avalore Rules Compliance

The implementation strictly follows Avalore rules:
- Stats/skills range: -3 to +3 ✓
- Check format: 2d10 + Stat + Skill ✓
- Base HP: 20 ✓
- Initiative: DEX-based ✓
- Actions per turn: 2 (default) ✓
- Item requirements: Stat+Skill thresholds ✓
- Backgrounds: Starting bonuses ✓
- XP advancement: Point-buy system ✓

## Conclusion

The Phase 1 implementation provides a solid foundation for the Avalore character simulator. The modular design, clear separation of concerns, and extensibility points make it straightforward to add combat mechanics, feats, spells, and other advanced features in future phases.
