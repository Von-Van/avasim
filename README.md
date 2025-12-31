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
# AvaSim

Combat sandbox and examples for Avalore-like rules, now modularized under the `combat/` package.

## Installation

- Python: 3.10+
- Install dependencies: `pip install -r requirements.txt`
  - Includes `PySide6` for the desktop UI and `streamlit` for the optional web UI.

## Project Structure

```
avasim/
  README.md
  requirements.txt
  __init__.py
  combat/               # modular combat engine package
    __init__.py
    engine.py
    participant.py
    map.py
    items.py
    feats.py
    spells.py
    enums.py
    dice.py
  phase2/
    combat.py
  tests.py
  streamlit_app.py      # optional web UI
  pyside_app.py         # desktop UI (PySide6)
```

## Quick Start (Library)

Import from `combat`:

```python
from combat.engine import CombatEngine
from combat.map import TacticalMap
from combat.participant import Participant

map_ = TacticalMap(width=10, height=10)
engine = CombatEngine(tactical_map=map_)

a = Participant(name="A", position=(1,1))
b = Participant(name="B", position=(2,1))

engine.add_participant(a)
engine.add_participant(b)

result = engine.attack(attacker=a, defender=b, weapon="sword")
print(result.summary)
```

## Running Tests

- Run: `python3 -m unittest -q`

## Optional UIs

- Desktop (PySide6): `python3 pyside_app.py`
- Web (Streamlit): `streamlit run streamlit_app.py`

If you don’t use Streamlit, keep `PySide6` only; otherwise both are installed via `requirements.txt`.

## Windows Build (PyInstaller)

For a double-clickable Windows app (no console):

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name AvaSim --icon icon.ico pyside_app.py
```

The `--onefile` build creates `dist/AvaSim.exe`. If you prefer faster startup, drop `--onefile` for an unpacked `--onedir` build.
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
