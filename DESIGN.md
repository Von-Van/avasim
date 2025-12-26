# Avalore Character Simulator - Design Documentation

## Overview

This document describes the architecture and design decisions for the Avalore character simulator, implementing both character creation/management and a complete combat simulation system based on official Avalore mechanics.

The system is divided into two main modules:
1. **Character System** (`avasim.py`) - Character creation, stats, skills, XP, backgrounds, and equipment
2. **Combat System** (`combat_system.py`) - Full combat mechanics including weapons, armor, shields, feats, magic, and turn-based combat resolution

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

## Combat System Design (`combat_system.py`)

The combat system implements the complete Avalore combat mechanics as specified in the official rules.

### Combat Classes

#### Weapon Class
Represents Avalore weapons with all combat properties:
- **Fixed damage** (not dice-based, per Avalore rules)
- **Accuracy bonus** (modifier to attack rolls)
- **Actions required** (1 or 2 actions to attack)
- **Range category** (melee, skirmishing, ranged)
- **Armor piercing** (bypasses armor soak)
- **Stat requirements** (e.g., STR:Athletics for greatswords)
- **Underwater usability** (crossbows work, bows don't)
- **Two-handed** flag (affects shield usage)

#### Armor Class
Armor with realistic trade-offs:
- **Light**: 1d2-1 protection (0-1), no penalties, perfect for agile characters
- **Medium**: 1d3-1 protection (0-2), -1 evasion, balanced option
- **Heavy**: 1d3 protection (1-3), -2 evasion, -3 stealth, -1 movement, prohibits bows
- **Stat requirements** (Heavy armor needs STR:Athletics 3); unmet requirements impose -2 movement and -1 soak

#### Shield Class
Active defense requiring Block action:
- **Small Shield**: 2d10-3 vs DC 12, requires DEX:Finesse 2 + STR:Athletics 2
- **Large Shield**: 2d10-2 vs DC 12, grants AP immunity, requires STR:Athletics 2 + STR:Fortitude 2
- **Ranged bonus**: +1 when blocking arrows/bolts

#### Feat Class
Special abilities with prerequisites:
- **Dual Striker**: Attack with two weapons as one action (-1 aim each)
- **Volley**: Fire two arrows with bow (-1 aim each, once per turn)
- **Quickfooted**: +3 to evasion rolls
- **Armor Piercer**: Make AP attacks with small/arming swords (limited action)
- **Riposte**: Counter-attack when enemy misses
- **Second Wind**: Gain temp HP = STR:Fortitude + 2 (once per fight)
- **Shieldmaster**: Enhanced shield blocking
- **Precise Senses**: No penalties in darkness

#### Spell Class
Magic system with Anima resource:
- **Anima cost** (resource depletion)
- **Casting DC 10** (easier than skill checks)
- **Casting roll**: 2d10 + HAR:Arcana
- **Miscast**: Fail = lose half Anima, no effect
- **Overcast**: Cast with 0 Anima, risk consequences (1d6 severity)

### Combat Resolution

#### Attack Sequence
1. **Attack Roll**: 2d10 + weapon accuracy + modifiers
2. **Critical Check**: Double 10s = auto-hit, AP, +2 damage if weapon is AP
3. **Evasion Check** (if defender evading):
   - Defender rolls 2d10 + DEX:Acrobatics + armor penalty
   - If evasion ≥ attack: Full dodge
   - If evasion ≥ 12 but < attack: **Grazing hit** (half damage for light armor, full for heavy)
   - If evasion < 12: Failed dodge
4. **Block Check** (if defender has shield up):
   - Roll 2d10 + shield modifier (+ ranged bonus if applicable)
   - Success (≥12): Block all damage
   - Failure: Attack proceeds
5. **Hit Check**: Attack total ≥ 12 to hit
6. **Damage Application**:
   - Apply weapon damage
   - Roll armor soak (unless AP)
   - Deduct from HP
   - Check for Critical status (0 HP)

#### Magic System
1. **Anima Check**: Has enough Anima or attempt overcast
2. **Casting Roll**: 2d10 + HAR:Arcana vs DC 10
3. **Success**: Apply spell effects, deduct Anima
4. **Miscast**: Lose half Anima, no effect
5. **Overcast Miscast**: Knocked unconscious, Anima → 0
6. **Overcast Success**: Spell works, roll 1d6 for consequence severity

### Combat Participant
Wraps Character with combat state:
- **HP tracking** (current/max)
- **Anima tracking** (current/max for mages)
- **Equipment** (weapon, armor, shield)
- **Combat status** (evading, blocking, critical)
- **Feats** with usage tracking
- **Position** (for range/movement)

### Combat Engine (AvaCombatEngine)
Manages full combat encounters:
- **Initiative system**: 2d10 + DEX, sorted descending
- **Turn order** with automatic advancement
- **Action economy**: 2 actions per turn (default)
- **Combat log**: Detailed event recording
- **Victory conditions**: Combat ends when one side eliminated

### Weapon Database
Complete Avalore weapon set:
- **Small weapons**: Dagger (3 dmg, small weapon slot)
- **Arming swords**: +1 hit, 4 dmg, 1 action
- **Finesse blades**: Rapier (4 dmg, requires DEX:Finesse 1)
- **Maces**: 5 dmg, heavy blunt
- **Greatswords**: 7 dmg, 2 actions, requires STR:Athletics 2
- **Polearms**: Spear (5 dmg, skirmishing range)
- **Javelins**: 4 dmg, works underwater
- **Slings**: 6 dmg, +1 hit, 2 actions
- **Longbow**: 6 dmg, 2 actions, can't use in heavy armor
- **Recurve Bow**: 5 dmg, 1 action
- **Crossbow**: 6 dmg, AP, works underwater
- **Unarmed**: 2 dmg, always available

### Design Principles

#### 1. Faithful to Source Material
All mechanics match official Avalore rules:
- 2d10 roll system (not d20)
- DC 12 for standard checks, DC 10 for magic
- Fixed weapon damage (not dice)
- Armor soak rolls (randomized protection)
- Grazing hit mechanics for partial dodges
- AP immunity from large shields

#### 2. Separation of Character and Combat
- `Character` class: Stats, skills, XP, persistence
- `CombatParticipant`: Wraps Character with combat state
- Clean interface between systems

#### 3. Extensible Feat System
Feats defined as data with behavior in combat engine:
- Easy to add new feats
- Prerequisite checking
- Usage tracking (per turn, per fight)

#### 4. Deterministic Except Dice
All mechanics are predictable except:
- Dice rolls (2d10, 1d3, etc.)
- Initiative order (ties broken by reroll)
This enables:
- Testing with seed control
- Replay of combat
- AI opponent development

#### 5. Comprehensive Logging
Combat engine logs every:
- Roll result with breakdown
- Decision made
- Effect applied
Enables debugging and player understanding

### Usage Examples

#### Basic Combat
```python
from avasim import create_character
from combat import CombatParticipant, AvaCombatEngine, AVALORE_WEAPONS, AVALORE_ARMOR

# Create characters
char1 = create_character("Warrior", "Soldier", starting_xp=20)
char2 = create_character("Mage", "Mage", starting_xp=20)

# Setup combat participants
warrior = CombatParticipant(
    character=char1,
    current_hp=20,
    max_hp=20,
    weapon_main=AVALORE_WEAPONS["Arming Sword"],
    armor=AVALORE_ARMOR["Heavy Armor"]
)

mage = CombatParticipant(
    character=char2,
    current_hp=18,
    max_hp=18,
    anima=8,
    max_anima=8,
    weapon_main=AVALORE_WEAPONS["Dagger"]
)

# Run combat
engine = AvaCombatEngine([warrior, mage])
engine.roll_initiative()

while not engine.is_combat_ended():
    current = engine.get_current_participant()
    # ... perform actions ...
    engine.advance_turn()
```

### Future Enhancements

Potential additions:
1. **Spell Book System**: Define full spell libraries per discipline
2. **Feat Interactions**: Complex feat combos (Dual Striker + Riposte)
3. **Environmental Factors**: Underwater combat, darkness, terrain
4. **Advanced AI**: Tactical decision-making for NPCs
5. **Status Effects**: Stunned, poisoned, blessed, cursed
6. **Movement System**: Grid-based positioning, opportunity attacks
7. **Death Saves**: Rolls when Critical to determine survival
8. **Rest System**: Short/long rests to restore HP and Anima

## Conclusion

The Phase 1 implementation provides a solid foundation for the Avalore character simulator. The modular design, clear separation of concerns, and extensibility points make it straightforward to add combat mechanics, feats, spells, and other advanced features in future phases.
