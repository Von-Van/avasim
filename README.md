# Avalore Character Simulator

A comprehensive Python-based simulator for the Avalore tabletop RPG, implementing complete character mechanics and a full combat system with weapons, armor, shields, feats, and magic.

## Features

### Character System
- **Stat System**: Four core stats (Dexterity, Intelligence, Harmony, Strength) with three skills each
- **Character Creation**: Build characters with customizable attributes
- **Backgrounds**: Apply background bonuses and traits (10 backgrounds)
- **Equipment System**: Equip items with requirements and stat modifiers
- **XP System**: Track experience and spend it to improve stats/skills
- **Persistence**: Save and load characters to/from JSON files
- **Derived Stats**: Automatic calculation of HP, initiative, and modifiers

### Combat System
- **Complete Weapon System**: 12+ weapon types with accurate Avalore stats
  - Small weapons (daggers), arming swords, finesse blades (rapiers)
  - Heavy weapons (maces, greatswords), polearms (spears)
  - Ranged weapons (bows, crossbows, slings, javelins)
  - Fixed damage, accuracy bonuses, action costs, armor piercing
- **Armor System**: Light, medium, and heavy armor with trade-offs
  - Randomized protection (1d2-1, 1d3-1, 1d3)
  - Evasion, stealth, and movement penalties
  - Stat requirements and unmet requirement penalties (-2 move, -1 soak)
- **Shield System**: Active blocking with small and large shields
  - Block rolls (2d10 + modifier vs DC 12)
  - AP immunity from large shields
- **Feat System**: Special abilities like Dual Striker, Volley, Quickfooted, Riposte
- **Magic System**: Complete spellcasting with Anima resource
  - Casting rolls (2d10 + HAR:Arcana vs DC 10)
  - Miscast mechanics
  - Overcasting with consequences
- **Combat Engine**: Full turn-based combat resolution
  - Initiative system (2d10 + DEX)
  - Attack resolution with evasion and blocking
  - Critical hits (double 10s)
  - Grazing hits for partial dodges
  - Armor soak mechanics
  - Comprehensive combat logging

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/Von-Van/avasim.git
cd avasim
python3 -m pip install -r requirements.txt
```

## Quick Start

### Character Creation

```python
from avasim import Character

# Create a new character
char = Character(name="Aria")

# Apply a background
char.apply_background("Soldier")

# Add some XP first
char.add_xp(20)

# Spend XP to improve stats
char.spend_xp_on_stat("Strength", 1)
char.spend_xp_on_skill("Strength", "Athletics", 1)

# Equip an item
from avasim import ITEMS
longbow = ITEMS["Longbow"]
char.equip_item(longbow)

# Save character
char.save_to_file("aria.json")

# Load character
loaded_char = Character.load_from_file("aria.json")
```

### Combat Simulation (programmatic)

```python
from avasim import create_character
from combat import (
  CombatParticipant,
  AvaCombatEngine,
  AVALORE_WEAPONS,
  AVALORE_ARMOR,
  AVALORE_SHIELDS
)

# Create characters
warrior_char = create_character("Aria", "Soldier", starting_xp=25)
warrior_char.spend_xp_on_stat("Strength", 2)
warrior_char.spend_xp_on_skill("Strength", "Athletics", 2)

mage_char = create_character("Zara", "Mage", starting_xp=25)
mage_char.spend_xp_on_stat("Harmony", 2)
mage_char.spend_xp_on_skill("Harmony", "Arcana", 3)

# Setup combat participants
warrior = CombatParticipant(
    character=warrior_char,
    current_hp=20,
    max_hp=20,
    weapon_main=AVALORE_WEAPONS["Arming Sword"],
    armor=AVALORE_ARMOR["Heavy Armor"],
    shield=AVALORE_SHIELDS["Large Shield"]
)

mage = CombatParticipant(
    character=mage_char,
    current_hp=18,
    max_hp=18,
    anima=8,
    max_anima=8,
    weapon_main=AVALORE_WEAPONS["Dagger"]
)

# Initialize combat
engine = AvaCombatEngine([warrior, mage])
engine.roll_initiative()

# Run combat turns
while not engine.is_combat_ended():
    current = engine.get_current_participant()
    
    # Determine target
    targets = [p for p in engine.participants if p != current and p.current_hp > 0]
    if targets:
        target = targets[0]
        
        # Perform action (attack or cast spell)
        if current == mage and mage.anima > 0:
            from combat import AVALORE_SPELLS
            engine.perform_cast_spell(mage, AVALORE_SPELLS["Force Bolt"], warrior)
        else:
            engine.perform_attack(current, target)
    
    engine.advance_turn()

# View results
print(engine.get_combat_summary())
```

## Avalore Rules Summary

### Stats and Skills

Characters have four stats (range -3 to +3):
- **Dexterity (DEX)**: Acrobatics, Stealth, Finesse
- **Intelligence (INT)**: Healing, Perception, Research
- **Harmony (HAR)**: Arcana, Nature, Belief
- **Strength (STR)**: Athletics, Fortitude, Forging

### Checks

Action checks use 2d10 + Stat + Skill modifiers.

### Combat

- **Attack Resolution**: 2d10 + accuracy vs DC 12 (or contested evasion roll)
- **Evasion**: 2d10 + DEX:Acrobatics (modified by armor penalties)
- **Blocking**: 2d10 + shield modifier vs DC 12
- **Critical Hits**: Double 10s = auto-hit with AP and bonus damage
- **Grazing Hits**: Partial dodge (evasion ≥12 but < attack) = reduced damage
- **Movement**: One free move up to 5 blocks each turn (penalties apply); Dash costs 1 action and grants +4 more blocks (total 9 with no penalties)
- **Armor Soak**: Light (1d2-1), Medium (1d3-1), Heavy (1d3)
- **Armor Piercing**: Bypasses armor soak entirely

### Magic

- **Casting**: 2d10 + HAR:Arcana vs DC 10
- **Anima Cost**: Each spell consumes Anima (mage resource)
- **Miscast**: Failed cast loses half Anima cost
- **Overcasting**: Cast with 0 Anima, risk severe consequences

### Derived Stats

- **HP**: Base 20 (modifiable by feats/items)
- **Initiative**: Based on DEX check
- **Actions**: 2 per turn (default)

## Combat Examples

The repository includes `combat_examples.py` with complete demonstrations:

1. **Basic Melee Combat**: Two warriors fighting with swords and armor
2. **Ranged Combat**: Archer vs knight with shield blocking
3. **Magic Combat**: Mage casting spells against a warrior
4. **Evasion Mechanics**: Agile rogue dodging attacks with Quickfooted feat
5. **Critical Hits & AP**: Crossbow piercing heavy armor
6. **Overcasting**: Desperate mage casting with no Anima

Run examples:
```bash
python combat_examples.py
```

### Desktop Combat Sandbox (PySide6)

Run the desktop UI to configure two combatants and simulate full combat rounds:

```bash
python3 pyside_app.py
```

Use the UI to set stats/skills, pick weapons/armor/shields, toggle evading/blocking, and click **Run full combat** to see the turn-by-turn log.

## Project Structure

```
avasim/
├── avasim.py              # Core character system
├── combat/                # Modular combat package (engine, items, feats, spells, map)
├── combat_examples.py     # Combat demonstrations
├── examples.py            # Character system examples
├── tests.py               # Test suite
├── pyside_app.py          # Desktop combat sandbox (PySide6)
├── equipment_data.py      # Sample equipment
├── DESIGN.md              # Architecture documentation
├── README.md              # This file
└── phase2/
  └── combat.py          # Early combat prototype
```

## Testing

```bash
python -m unittest tests
```

## Documentation

- [DESIGN.md](DESIGN.md) - Complete architecture and design decisions
- [combat_examples.py](combat_examples.py) - Working combat scenarios
- [examples.py](examples.py) - Character creation examples

## Avalore Rules Compliance

This simulator faithfully implements official Avalore mechanics:
- ✓ 2d10 roll system (not d20)
- ✓ Stats and skills range -3 to +3
- ✓ DC 12 for standard checks, DC 10 for magic
- ✓ Fixed weapon damage (not dice-based)
- ✓ Armor soak with random protection rolls
- ✓ Evasion with grazing hit mechanics
- ✓ Shield blocking system
- ✓ Critical hits on double 10s
- ✓ Armor piercing mechanics
- ✓ Anima-based magic system
- ✓ Feat prerequisites and effects
- ✓ Equipment stat requirements

## License

This project implements mechanics from the Avalore RPG system.
