"""
AvaSim UI module - Professional theming, components, and visualization.

This module provides all UI-related functionality including:
- Theme management and styling
- Reusable UI components
- Animation and feedback effects
- Advanced map visualization
"""

# Theme and styling
from .theme import (
    Theme,
    ColorPalette,
    FontConfig,
    IconProvider,
    ThemeManager,
)

# Components and animations
from .animations import (
    ProgressIndicator,
    TextHighlighter,
    StatusBadge,
    AnimatedButton,
    TabTransitionHelper,
    TooltipEnhancer,
    IconButtonWithLabel,
)

from .components import (
    LabeledComboBox,
    LabeledSpinBox,
    LabeledLineEdit,
    IconButton,
    SectionGroupBox,
    ControlRow,
    CollapsibleSection,
)

# Map visualization
from .map_widget import (
    TacticalMapWidget,
    MapLegend,
)

__all__ = [
    # Theme
    "Theme",
    "ColorPalette",
    "FontConfig",
    "IconProvider",
    "ThemeManager",
    # Animations
    "ProgressIndicator",
    "TextHighlighter",
    "StatusBadge",
    "AnimatedButton",
    "TabTransitionHelper",
    "TooltipEnhancer",
    "IconButtonWithLabel",
    # Components
    "LabeledComboBox",
    "LabeledSpinBox",
    "LabeledLineEdit",
    "IconButton",
    "SectionGroupBox",
    "ControlRow",
    "CollapsibleSection",
    # Map
    "TacticalMapWidget",
    "MapLegend",
]
