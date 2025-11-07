# Avalore Character Simulator

A Python-based character simulator for the Avalore tabletop RPG, implementing core character mechanics including stats, skills, backgrounds, items, and character persistence.

## Features

- **Stat System**: Four core stats (Dexterity, Intelligence, Harmony, Strength) with three skills each
- **Character Creation**: Build characters with customizable attributes
- **Backgrounds**: Apply background bonuses and traits
- **Equipment System**: Equip items with requirements and stat modifiers
- **XP System**: Track experience and spend it to improve stats/skills
- **Persistence**: Save and load characters to/from JSON files
- **Derived Stats**: Automatic calculation of HP, initiative, and modifiers

## Installation

No external dependencies required. Uses Python 3.6+.

```bash
git clone https://github.com/Von-Van/avasim.git
cd avasim
```

## Quick Start

```python
from avasim import Character

# Create a new character
char = Character(name="Aria")

# Apply a background
char.apply_background("Soldier")

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

## Avalore Rules Summary

### Stats and Skills

Characters have four stats (range -3 to +3):
- **Dexterity (DEX)**: Acrobatics, Stealth, Finesse
- **Intelligence (INT)**: Healing, Perception, Research
- **Harmony (HAR)**: Arcana, Nature, Belief
- **Strength (STR)**: Athletics, Fortitude, Forging

### Checks

Action checks use 2d10 + Stat + Skill modifiers.

### Derived Stats

- **HP**: Base 20 (modifiable by feats/items)
- **Initiative**: Based on DEX check
- **Actions**: 2 per turn (default)

## Testing

```bash
python -m pytest tests/
```

## License

This project implements mechanics from the Avalore tabletop RPG system.
