# AvaSim Project Structure

## Directory Organization

```
avasim/
├── combat/                 # Core combat simulation engine
│   ├── __init__.py
│   ├── engine.py          # Main combat engine
│   ├── participant.py     # Character combat state
│   ├── items.py           # Weapons, armor, shields
│   ├── feats.py           # 30+ combat feats
│   ├── spells.py          # Spellcasting mechanics
│   ├── map.py             # Tactical grid system
│   ├── dice.py            # 2d10 dice roller
│   └── enums.py           # Game constants
│
├── ui/                     # Professional UI components
│   ├── __init__.py        # Main UI module exports
│   ├── theme.py           # Theming & styling system
│   ├── animations.py      # Effects & feedback
│   ├── components.py      # Reusable UI widgets
│   └── map_widget.py      # Tactical map visualization
│
├── avasim.py              # Character definition
├── character.py           # Character sheet structure
├── pyside_app.py          # Main desktop application
├── examples.py            # Usage examples
├── test_combat.py         # Unit tests (18 tests)
├── test_tactical_map.py   # Map system tests
└── requirements.txt       # Python dependencies
```

## Module Breakdown

### Combat Module (`combat/`)
Implements all Avalore RPG mechanics:
- **engine.py**: Main combat simulation loop, action resolution
- **participant.py**: Character state, action economy, HP tracking
- **items.py**: All 21 weapons, armor types, shields
- **feats.py**: 30+ feats with action costs and once-per-turn limits
- **spells.py**: Spellcasting, anima costs, miscast mechanics
- **map.py**: 10×10 grid, occupant tracking, distance calculations
- **dice.py**: 2d10 system with critical/graze detection
- **enums.py**: ActionType, DamageType, StatusEffect, etc.

### UI Module (`ui/`)
Professional PySide6 interface components:
- **theme.py**: Dark/Light themes, color palettes, font system, icons
- **animations.py**: Progress indicators, text highlighting, status badges
- **components.py**: Reusable labeled widgets, buttons, group boxes
- **map_widget.py**: Professional tactical map graphics, legend
- **__init__.py**: Clean exports for easy importing

### Root Level
- **pyside_app.py**: Main application window, event handling
- **avasim.py**: Character class definition
- **character.py**: Character sheet template structure
- **examples.py**: Combat scenario examples
- **test_*.py**: Comprehensive unit tests
- **requirements.txt**: Dependencies (PySide6, qtawesome, streamlit)

## Import Patterns

### Clean UI Imports
```python
from ui import (
    Theme, ThemeManager,          # Theming
    IconProvider, FontConfig,      # Design system
    ProgressIndicator,             # Animations
    TextHighlighter,               # Log formatting
    TacticalMapWidget,             # Map visualization
    LabeledComboBox, IconButton,   # Components
)
```

### Combat Imports
```python
from combat import (
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
)
from combat.enums import ActionType, StatusEffect
```

## File Organization Benefits

✅ **Logical Grouping**: Related code organized into modules  
✅ **Easy Navigation**: Clear folder structure makes finding code simple  
✅ **Reusability**: UI components can be reused across projects  
✅ **Testability**: Isolated modules are easier to unit test  
✅ **Maintainability**: Changes contained within module boundaries  
✅ **Scalability**: New features easily added to appropriate modules  
✅ **Clean Imports**: Main files import only what they need  

## Adding New Features

### New UI Component
1. Add to `ui/components.py`
2. Export in `ui/__init__.py`
3. Import in `pyside_app.py`

### New Combat Feat
1. Add to `combat/feats.py`
2. Register in `combat/engine.py`
3. Add tests to `test_combat.py`

### New Map Feature
1. Add to `combat/map.py` or `ui/map_widget.py`
2. Update `TacticalMapWidget.draw_snapshot()` if visual
3. Add tests to `test_tactical_map.py`

## Deprecated Files
The following files in the root directory are now superseded by the ui/ module:
- `ui_theme.py` → `ui/theme.py`
- `ui_animations.py` → `ui/animations.py`
- `ui_components.py` → `ui/components.py`
- `ui_map_widget.py` → `ui/map_widget.py`

These can be safely deleted once you confirm everything works correctly.
