# AvaSim - Avalore Combat Simulator

A comprehensive Python-based combat simulator for the Avalore tabletop RPG. Implements complete action economy, weapons system, armor and shields, 30+ combat feats, spellcasting, and tactical map combat.

## Quick Start

### Installation
```bash
pip install -r requirements.txt
python3 pyside_app.py
```

### Running Tests
```bash
python3 -m unittest test_combat -v
```

All 18 tests pass, covering weapons, armor, feats, action economy, and combat mechanics.

## Features

### Action Economy
- **2 Actions + 1 Limited Action per turn** - Enforced globally across all actions
- **First Strike feat** - Grants 3 actions on turn 1 only
- **Action consumption tracking** - All abilities consume appropriate actions
- **Once-per-turn/scene limits** - Feats respect limited action constraints
- **Block/Evade mutual exclusivity** - Cannot block AND evade same turn
- **Death saves** - Triggered at 0 HP, once per scene

### Weapons (21 Types)
All weapons match official Avalore rules with fixed damage, accuracy, and action costs.

| Weapon | Damage | Accuracy | Actions | Special |
|--------|--------|----------|---------|---------|
| Unarmed Strike | 1 | 0 | 1 | — |
| Small Weapon (Dagger) | 2 | 0 | 1 | — |
| Arming Sword | 3 | 0 | 1 | — |
| Rapier | 3 | +1 | 1 | Finesse |
| Mace | 4 | 0 | 1 | — |
| Greatsword | 8 | 0 | 2 | Requires lift |
| Polearm | 6 | +1 | 1 | Reach 2 |
| Staff | 2 | 0 | 1 | 2-handed, can dex |
| Spear | 4 | 0 | 1 | Reach 1 |
| Whip | 2 | 0 | 1 | Reach 2, can disarm |
| Meteor Hammer | 5 | 0 | 2 | Requires lift |
| Throwing Knife | 2 | 0 | 1 | Ranged (3 blocks) |
| Recurve Bow | 4 | 0 | 2 | Ranged (5 blocks) |
| Longbow | 5 | +1 | 2 | Ranged (6 blocks) |
| Crossbow | 5 | +1 | 1 | Ranged (5 blocks), load required |
| Sling | 3 | 0 | 2 | Ranged (4 blocks) |
| Javelin | 3 | 0 | 1 | Ranged (3 blocks) |
| Arcane Wand | 2 | +1 | 1 | Spellcasting focus |
| Spellbook | 0 | 0 | 0 | Spellcasting focus |
| Large Shield | 2 | 0 | 1 | Block 2d10+2 vs DC 12, AP immune |
| Holy Symbol | 2 | 0 | 1 | Spellcasting focus |

**Weapon Requirements:**
- Heavy/2-action weapons need a **lift action** before attacking (uses 1 limited action per scene)
- Unmet stat requirements apply **-2 accuracy penalty**
- Crossbows require a **load action** between shots
- Ranged weapons blocked by heavy armor (armor provides "no ranged weapons" prohibition)

### Armor System (3 Types)
| Armor | Soak | Evasion Penalty | Stealth Penalty | Movement Penalty |
|-------|------|-----------------|-----------------|-----------------|
| Light | 1d2-1 | — | — | — |
| Medium | 1d3-1 | -1 | -2 | -1 |
| Heavy | 1d3 | -2 | -3 | -2 |

**Special Rules:**
- **Armor Piercing (AP)**: Bypasses soak entirely
- **Graze mechanic**: Evasion ≥12 but <attack = half damage (soak still applies)
- **Heavy armor prohibition**: Blocks ranged weapons (bows, slings, javelins, throwing knives)

### Shields
- **Small Shield**: Block 2d10 vs DC 12
- **Large Shield**: Block 2d10+2 vs DC 12, immune to AP damage

### Combat Resolution

**Attack Flow:**
1. Attacker rolls 2d10 + accuracy vs defender's evasion DC or contested roll
2. Double 10s = critical hit (auto-hit, +2 damage, bypasses soak)
3. Evasion ≥12 but <attack = graze (half damage, soak still applies)
4. Success = full damage roll
5. Armor soak (if not AP) reduces damage
6. If HP drops to 0, trigger death save (once per scene)

**Key Mechanics:**
- **Initiative**: 2d10 + DEX:Acrobatics modifier
- **Evasion DC**: Contested 2d10 + DEX:Acrobatics vs attack roll
- **Block**: Active defense, 2d10 + shield mod vs DC 12 (mutual exclusive with evade)
- **Dash**: 1 action, +4 blocks movement (total 9 with no penalties vs 5 base)
- **Death Save**: 2d10 + HAR:Belief vs DC 12 (at 0 HP), once per combat scene

### Combat Feats (30+)

All feats respect action economy and once-per-turn/scene limits:

| Feat | Type | Effect |
|------|------|--------|
| **Momentum Strike** | Active | +2 dmg if you've hit target this turn (1 action) |
| **Feint** | Limited | Enemy -2 to evade next attack this turn (limited action) |
| **Piercing Strike** | Active | Ignore armor soak, but -2 to accuracy (1 action) |
| **Ranger's Gambit** | Active | Attack two different targets within 3 blocks (2 actions) |
| **Trick Shot** | Active | Ricochet attack through cover/allies (1 action, 2 ranged damage) |
| **Two Birds One Stone** | Active | Attack two nearby targets, split damage (1 action) |
| **Dual Striker** | Limited | Extra attack with off-hand weapon if dual wielding (limited) |
| **Volley** | Active | Rapid fire: 3 shots at -3 accuracy each (2 actions) |
| **Armor Piercer** | Limited | Next attack ignores armor this turn (limited action) |
| **Bastion Stance** | Active | Block 2 attacks this turn (1 action, mutual exclusive with evade) |
| **Hamstring** | Active | Target -1 to movement next turn (1 action) |
| **Patient Flow** | Limited | Spend limited action to increase evasion by 2 this turn (limited) |
| **Quickdraw** | Limited | Draw ranged weapon as free action when dashing (limited) |
| **Vicious Mockery** | Active | INT:Perception check deals 1 psychic damage + target -1 next turn (1 action) |
| **Galestorm** | Active | Move 5 blocks for free, trigger whirling strikes on adjacent enemies (1 action) |
| **Fanning Blade** | Active | Arc attack hits 3 enemies around caster, -1 accuracy (2 actions) |
| **Lacuna** | Limited | Nullify one magical effect this turn (limited action) |
| **Harmonious Deflection** | Limited | Reflect spell back at caster (limited action, requires HAR check) |
| **Quickfooted** | Passive | +2 to evasion, +1 to movement |
| **First Strike** | Passive | 3 actions on turn 1 of combat only |
| **Heavy Hitter** | Passive | +2 damage with 2-action weapons |
| **Aggressive Stance** | Passive | +1 accuracy but -1 to evasion |
| **Defensive Stance** | Passive | +2 evasion but -1 accuracy |
| **Dual Wielder** | Passive | Can equip two weapons, off-hand at -2 accuracy |
| **Two-Handed Mastery** | Passive | +1 accuracy with 2-handed weapons |
| **Shield Mastery** | Passive | +2 to block rolls |
| **Riposte** | Limited | Counterattack after successful block (limited, not same target) |
| **Acrobatic Escape** | Limited | Free movement away from one enemy (limited action) |
| **Power Strike** | Limited | +4 damage, -2 accuracy (limited action) |
| **Whirling Devil** | Passive | Moving triggers attack on all adjacent enemies |

### Spellcasting
- **Casting**: 2d10 + HAR:Arcana vs DC 10
- **Anima**: Spells consume Anima (mage resource)
- **Miscast**: Failed spell costs half Anima
- **Overcasting**: Cast with 0 Anima at risk of consequences

### Tactical Map
- **Grid-based positioning**: 2D tile-based combat map
- **Distance/reach calculations**: Block-based distances
- **Movement penalties**: Applied based on armor type
- **Ranged weapon ranges**: Each weapon has defined reach

## Desktop GUI (PySide6)

Run the interactive combat simulator:
```bash
python3 pyside_app.py
```

**Features:**
- Create two combatants with stats/skills/weapons/armor
- Configure feats and special abilities
- 3 simulation modes:
  - Computer controls both
  - Player controls both
  - Player controls one, computer controls other
- Turn-by-turn combat log with detailed action resolution
- Full weapon/armor/feat tooltips
- Combat history and statistics

## Code Architecture

### Module Structure

**Combat Module** (`combat/`)

[combat/engine.py](combat/engine.py) - **Core combat engine (1690+ lines)**
- `CombatEngine`: Main combat orchestrator
- Turn management and initiative
- Action resolution and validation
- All 30+ feat implementations
- Attack/damage/block resolution
- Combat state tracking

[combat/participant.py](combat/participant.py) - **Character state during combat**
- `Participant`: Combat character state
- Action economy tracking (2 actions + 1 limited)
- Armor soak and graze calculations
- Weapon requirement validation
- Block/evade mutual exclusivity enforcement
- Death save mechanics

[combat/items.py](combat/items.py) - **Weapons, armor, shields**
- 21 weapon definitions with Avalore stats
- 3 armor types with penalties
- 2 shield types with modifiers
- Weapon requirements and special properties

[combat/feats.py](combat/feats.py) - **Feat definitions**
- 30+ feat class definitions
- Prerequisites and effects
- Action costs and limitations

[combat/spells.py](combat/spells.py) - **Spellcasting system**
- Spell definitions with Anima costs
- Casting mechanics and miscast rules
- Overcasting consequences

[combat/map.py](combat/map.py) - **Tactical grid system**
- Grid-based positioning
- Distance calculations
- Reach validation

[combat/enums.py](combat/enums.py) - **Game constants**
- Action types, damage types, armor types
- Spell schools, condition types

[combat/dice.py](combat/dice.py) - **Dice rolling utilities**
- 2d10 roller with Avalore rules
- Critical/graze detection

**UI Module** (`ui/`)

[ui/theme.py](ui/theme.py) - **Professional theming system**
- `Theme` enum (Dark/Light modes)
- `ThemeManager` - generates 400+ line QSS stylesheets
- `ColorPalette` - 13-color palettes for consistent design
- `FontConfig` - standardized typography across app
- `IconProvider` - Font Awesome icon management (30+ icons)

[ui/animations.py](ui/animations.py) - **Visual effects and feedback**
- `ProgressIndicator` - smooth animated progress bars
- `TextHighlighter` - 7-category syntax highlighting for combat logs
- `StatusBadge` - animated status indicators with pulsing effects
- `AnimatedButton`, `TabTransitionHelper`, `TooltipEnhancer` - helper components

[ui/components.py](ui/components.py) - **Reusable UI widgets**
- `LabeledComboBox`, `LabeledSpinBox`, `LabeledLineEdit` - consistent input controls
- `IconButton` - buttons with Font Awesome icons
- `SectionGroupBox` - professional grouped control containers
- `ControlRow` - flexible horizontal control layouts

[ui/map_widget.py](ui/map_widget.py) - **Tactical map visualization**
- `TacticalMapWidget` - 32×32 cell graphics widget with professional rendering
- `MapLegend` - interactive map legend with terrain/position indicators
- Grid-based map display with color-coded terrain
- Position highlighting system (active/target/occupant)

## UI/UX Features (Desktop Application)

The PySide6-based desktop application provides a professional, polished interface:

### Visual Design
- **Professional Theme System** - Centralized color management with Dark/Light theme toggle
- **Font Awesome Icons** - 30+ consistent icons throughout the application for visual clarity
- **Improved QSS Styling** - Modern stylesheet with proper contrast, rounded corners, and hover effects
- **Better Visual Hierarchy** - Organized control groups with GroupBox sections for improved scannability
- **Theme-aware Components** - Tab bars, buttons, and menus now properly respect the current theme

### Layout Improvements
- **Organized Control Sections** - Simulation settings grouped into logical "Simulation Settings" and "Combat State" sections
- **Better Spacing** - Increased padding and margins for improved readability
- **Responsive Widgets** - Combo boxes and controls properly sized with maximum widths to prevent cramping
- **Scroll Areas** - Character editor and simulation tab wrapped in scroll areas for small screens

### Interactive Enhancements
- **Better Button Styling** - Clear hover states with visual feedback (color changes, border highlights)
- **Improved Checkboxes** - Custom styled with better visibility and hover effects
- **Professional Sliders** - Custom-styled replay slider with accent color
- **Keyboard Navigation** - Full tab support and shortcut indicators

### User Experience
- **Quick Start Features** - "Start", "Quick Start Duel", and "Reload last setup" buttons for fast access
- **Contextual Tooltips** - Helpful tooltips on controls explaining their function
- **Persistent Settings** - Theme, layout, and character templates saved between sessions
- **Clean Logs** - Color-coded action logs (red for critical hits, orange for hits, gray for misses, blue for movement)

### Professional Code Organization
All UI code is now organized in the clean `/ui/` module structure:
- **ui/theme.py** - Centralized theme and styling system
- **ui/animations.py** - Animations, effects, and progress indicators
- **ui/components.py** - Reusable widgets and controls
- **ui/map_widget.py** - Professional tactical map visualization
- **ui/__init__.py** - Single import point for all UI components

This organization provides:
- ✅ Clean separation of concerns
- ✅ Easy code navigation and maintenance
- ✅ Reusable components for future projects
- ✅ Professional import patterns (`from ui import ...`)

## Testing

All 18 tests pass:
```
test_combat_participant.py:
  ✓ test_consume_action_standard
  ✓ test_consume_action_limited
  ✓ test_consume_action_insufficient
  ✓ test_death_save_triggered
  ✓ test_block_evade_exclusivity
  ✓ test_weapon_requirement_penalty
  ✓ test_can_use_weapon_checks

test_combat_mechanics.py:
  ✓ test_harmonized_arsenal_throw
  ✓ test_attack_graze_mechanics
  ✓ test_armor_soak_reduction
  ✓ test_critical_hit_ap
  ✓ test_feat_momentum_strike
  ✓ test_feat_dual_striker
  ✓ test_feat_armor_piercer
  ✓ test_feat_bastion_stance
  ✓ test_feat_galestorm
  ✓ test_feat_dual_wielder
  ✓ test_combat_engine_initialization

Ran 18 tests in 0.003s - OK
```

Test coverage includes:
- Action economy enforcement (action consumption)
- Weapon system (all 21 types, requirements, penalties)
- Armor system (soak, penalties, prohibitions)
- Shield mechanics (blocking)
- Feat mechanics (30+ feats with limits)
- Critical hits and graze damage
- Death saves
- Dual wielding and two-handed weapons
- Combat resolution flow

## File Guide

| File | Purpose |
|------|---------|
| [combat/engine.py](combat/engine.py) | Core combat simulation engine |
| [combat/participant.py](combat/participant.py) | Character state and action tracking |
| [combat/items.py](combat/items.py) | Weapon, armor, shield definitions |
| [combat/feats.py](combat/feats.py) | Feat system and effects |
| [combat/spells.py](combat/spells.py) | Spellcasting mechanics |
| [combat/map.py](combat/map.py) | Tactical grid system |
| [combat/dice.py](combat/dice.py) | Dice rolling and probability |
| [combat/enums.py](combat/enums.py) | Game constants and types |
| [ui/theme.py](ui/theme.py) | Theme management and styling |
| [ui/animations.py](ui/animations.py) | Visual effects and animations |
| [ui/components.py](ui/components.py) | Reusable UI widgets |
| [ui/map_widget.py](ui/map_widget.py) | Tactical map visualization |
| [ui/__init__.py](ui/__init__.py) | UI module exports |
| [pyside_app.py](pyside_app.py) | Desktop GUI (PySide6) |
| [test_combat.py](test_combat.py) | Unit tests (18 tests) |
| [DESIGN.md](DESIGN.md) | Architecture documentation |

## Avalore Rules Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| 2d10 roll system | ✓ Complete | All rolls use 2d10 + modifiers |
| Stats/skills (-3 to +3) | ✓ Complete | 4 stats, 3 skills each |
| DC 12 standard checks | ✓ Complete | Attacks vs evasion, blocks vs DC 12 |
| DC 10 magic checks | ✓ Complete | Spellcasting vs DC 10 |
| Fixed weapon damage | ✓ Complete | All 21 weapons with exact Avalore damage |
| Armor soak (random) | ✓ Complete | Light 1d2-1, Medium 1d3-1, Heavy 1d3 |
| Evasion/grazing | ✓ Complete | Contested rolls with graze mechanic |
| Shield blocking | ✓ Complete | Active block with small/large shields |
| Critical hits (10-10) | ✓ Complete | Auto-hit with +2 dmg, AP bypass |
| Armor piercing | ✓ Complete | Ignores soak, bypasses graze |
| Action economy (2+1) | ✓ Complete | Enforced globally, First Strike exception |
| Feat system | ✓ Complete | 30+ feats with action costs/limits |
| Once-per-turn limits | ✓ Complete | Limited actions tracked per turn |
| Once-per-scene limits | ✓ Complete | Death saves, lift/load once per scene |
| Spellcasting | ✓ Complete | Anima costs, miscast, overcasting |
| Initiative system | ✓ Complete | 2d10 + DEX:Acrobatics |
| Tactical map | ✓ Complete | Grid-based positioning and reach |
| Heavy armor restrictions | ✓ Complete | No ranged weapons with heavy armor |
| Weapon requirements | ✓ Complete | -2 accuracy penalty if unmet |
| Block/evade exclusivity | ✓ Complete | Cannot do both in same turn |
| Death saves | ✓ Complete | Triggered at 0 HP, once per scene |

## Combat Example

```python
from combat.engine import CombatEngine
from combat.participant import Participant
from combat.items import AVALORE_WEAPONS, AVALORE_ARMOR, AVALORE_SHIELDS

# Create combatants
warrior = Participant(
    name="Warrior",
    weapon=AVALORE_WEAPONS["Greatsword"],
    armor=AVALORE_ARMOR["Heavy Armor"],
    shield=AVALORE_SHIELDS["Large Shield"],
    stats={"dex": 1, "int": -1, "har": 0, "str": 2}
)

mage = Participant(
    name="Mage",
    weapon=AVALORE_WEAPONS["Arcane Wand"],
    armor=AVALORE_ARMOR["Light Armor"],
    stats={"dex": 0, "int": 1, "har": 2, "str": -2}
)

# Initialize and run combat
engine = CombatEngine([warrior, mage])
engine.roll_initiative()

while not engine.is_combat_ended():
    current = engine.get_current_participant()
    targets = [p for p in engine.participants if p != current and p.current_hp > 0]
    
    if targets:
        target = targets[0]
        engine.perform_attack(current, target)
    
    engine.advance_turn()

print(engine.get_combat_log())
```

## License

This project implements mechanics from the Avalore RPG system.
