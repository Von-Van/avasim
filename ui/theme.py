"""
Fantasy RPG theming and styling system for AvaSim UI.
Provides centralized color management, icons, QSS stylesheet generation, and texture integration.
"""

from enum import Enum
from typing import Dict, Tuple
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QFontDatabase
from PySide6.QtWidgets import QApplication, QStyle
import qtawesome as qta

# Import texture generator (will be available after all files are created)
try:
    from ui.texture_generator import TextureGenerator, get_cached_texture
except ImportError:
    # Fallback if texture_generator not available yet
    TextureGenerator = None
    get_cached_texture = None


class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"


def load_fantasy_fonts():
    """Load custom fantasy fonts from the fonts directory at application startup."""
    font_dir = Path(__file__).parent / "fonts"

    if not font_dir.exists():
        return  # Directory doesn't exist, use fallbacks

    fonts_to_load = [
        "Cinzel-Regular.ttf",
        "Cinzel-Bold.ttf",
        "CrimsonText-Regular.ttf",
        "CrimsonText-Bold.ttf",
        "Spectral-Regular.ttf",
        "Spectral-SemiBold.ttf",
        "Marcellus-Regular.ttf",
    ]

    for font_file in fonts_to_load:
        font_path = font_dir / font_file
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))


class ColorPalette:
    """Centralized color definitions for fantasy RPG theming."""

    # Dark theme colors - Gothic medieval aesthetic
    DARK = {
        "bg_primary": "#1a1410",        # Deep charcoal/brown
        "bg_secondary": "#2d2519",      # Rich dark brown (panels)
        "bg_tertiary": "#3d3226",       # Lighter brown (hover)
        "text_primary": "#e8dcc4",      # Aged parchment text
        "text_secondary": "#a89579",    # Faded gold/tan
        "accent": "#d4af37",            # Rich gold (primary accent)
        "accent_hover": "#f4cf47",      # Bright gold
        "accent_dark": "#8b7355",       # Bronze/dark gold
        "border": "#5c4a32",            # Dark bronze border
        "border_ornate": "#d4af37",     # Gold ornate borders
        "success": "#5a8359",           # Forest green
        "warning": "#b8621b",           # Rust orange
        "error": "#8b2e2e",             # Dark crimson
        "info": "#3a5a7a",              # Slate blue
    }

    # Light theme colors - Illuminated manuscript aesthetic
    LIGHT = {
        "bg_primary": "#e8dcc4",        # Parchment
        "bg_secondary": "#f5ede0",      # Lighter parchment
        "bg_tertiary": "#d4c4a8",       # Aged paper
        "text_primary": "#2d1f0f",      # Dark brown ink
        "text_secondary": "#5c4a32",    # Faded ink
        "accent": "#8b4513",            # Saddle brown
        "accent_hover": "#a0522d",      # Sienna
        "accent_dark": "#654321",       # Dark brown
        "border": "#8b7355",            # Medium brown
        "border_ornate": "#8b4513",     # Dark brown ornate
        "success": "#2d5a2d",           # Dark green
        "warning": "#b8621b",           # Rust
        "error": "#8b2e2e",             # Dark red
        "info": "#2a4a6a",              # Deep blue
    }


class FontConfig:
    """Font configurations for fantasy RPG UI elements."""

    @staticmethod
    def get_font(style: str, size: int = 11) -> QFont:
        """Get a configured font for specific UI style."""
        font = QFont()

        if style == "default":
            # Body text and UI labels - readable serif
            font.setFamilies(["Spectral", "Marcellus", "Georgia", "Times New Roman", "serif"])
            font.setPointSize(size)
        elif style == "heading":
            # Headings and titles - ornate medieval
            font.setFamilies(["Cinzel", "Crimson Text", "Georgia", "Times New Roman", "serif"])
            font.setPointSize(size)
            font.setBold(True)
        elif style == "subheading":
            # Subheadings - medium weight fantasy
            font.setFamilies(["Crimson Text", "Spectral", "Georgia", "serif"])
            font.setPointSize(size)
            font.setWeight(600)
        elif style == "monospace":
            # Logs and code - keep monospace but slightly stylized
            font.setFamilies(["Courier New", "Courier", "monospace"])
            font.setPointSize(size)
            font.setStyleStrategy(QFont.PreferAntialias)
        elif style == "small":
            # Small text - readable serif
            font.setFamilies(["Marcellus", "Spectral", "Georgia", "serif"])
            font.setPointSize(size)

        return font


def _safe_icon(primary: str, fallback: str = "") -> QIcon:
    """Try to create a qtawesome icon, falling back gracefully."""
    try:
        return qta.icon(primary)
    except Exception:
        if fallback:
            try:
                return qta.icon(fallback)
            except Exception:
                pass
        return QIcon()


class IconProvider:
    """Provides Font Awesome icons with theming support."""
    
    # Icon definitions — lazy loaded to avoid warning before QApplication exists
    _ICON_DEFS = {
        "play": ("fa6s.play", "fa.play"),
        "pause": ("fa6s.pause", "fa.pause"),
        "stop": ("fa6s.stop", "fa.stop"),
        "settings": ("fa6s.gear", "fa.cog"),
        "save": ("fa6s.floppy-disk", "fa.save"),
        "load": ("fa6s.folder-open", "fa.folder-open"),
        "export": ("fa6s.arrow-up-from-bracket", "fa.arrow-circle-o-up"),
        "add": ("fa6s.plus", "fa.plus"),
        "delete": ("fa6s.trash-can", "fa.trash-o"),
        "edit": ("fa6s.pen", "fa.pencil"),
        "copy": ("fa6s.copy", "fa.copy"),
        "undo": ("fa6s.rotate-left", "fa.undo"),
        "redo": ("fa6s.rotate-right", "fa.repeat"),
        "search": ("fa6s.magnifying-glass", "fa.search"),
        "refresh": ("fa6s.arrows-rotate", "fa.refresh"),
        "info": ("fa6s.circle-info", "fa.info-circle"),
        "warning": ("fa6s.triangle-exclamation", "fa.warning"),
        "error": ("fa6s.circle-xmark", "fa.times-circle"),
        "success": ("fa6s.circle-check", "fa.check-circle"),
        "arrow_up": ("fa6s.arrow-up", "fa.arrow-up"),
        "arrow_down": ("fa6s.arrow-down", "fa.arrow-down"),
        "arrow_left": ("fa6s.arrow-left", "fa.arrow-left"),
        "arrow_right": ("fa6s.arrow-right", "fa.arrow-right"),
        "menu": ("fa6s.bars", "fa.bars"),
        "close": ("fa6s.xmark", "fa.times"),
        "star": ("fa6s.star", "fa.star"),
        "heart": ("fa6s.heart", "fa.heart"),
        "shield": ("fa6s.shield-halved", "fa.shield"),
        "sword": ("fa6s.hand-fist", "fa.shield"),
        "person": ("fa6s.user", "fa.user"),
        "users": ("fa6s.users", "fa.users"),
        "map": ("fa6s.map", "fa.map"),
        "fire": ("fa6s.fire", "fa.fire"),
        "zap": ("fa6s.bolt", "fa.bolt"),
        "sun": ("fa6s.sun", "fa.sun-o"),
        "moon": ("fa6s.moon", "fa.moon-o"),
        "dice": ("fa6s.dice-d20", "fa.cube"),
        "chart": ("fa6s.chart-bar", "fa.bar-chart"),
        "expand": ("fa6s.chevron-down", "fa.chevron-down"),
        "collapse": ("fa6s.chevron-right", "fa.chevron-right"),
        "target": ("fa6s.crosshairs", "fa.crosshairs"),
        "skull": ("fa6s.skull", "fa.times"),
    }
    _cache: dict[str, QIcon] = {}
    
    @staticmethod
    def get_icon(name: str) -> QIcon:
        """Get an icon by name (lazy-loaded to avoid QApplication warning)."""
        if name not in IconProvider._cache:
            defs = IconProvider._ICON_DEFS.get(name)
            if defs:
                IconProvider._cache[name] = _safe_icon(defs[0], defs[1])
            else:
                IconProvider._cache[name] = QIcon()
        return IconProvider._cache[name]


class ThemeManager:
    """Manages theme switching and stylesheet generation."""
    
    def __init__(self, current_theme: Theme = Theme.DARK):
        self.current_theme = current_theme
    
    def get_palette(self) -> Dict[str, str]:
        """Get current theme's color palette."""
        if self.current_theme == Theme.DARK:
            return ColorPalette.DARK
        else:
            return ColorPalette.LIGHT
    
    def set_theme(self, theme: Theme):
        """Switch to a different theme."""
        self.current_theme = theme
    
    def generate_stylesheet(self) -> str:
        """Generate QSS stylesheet for fantasy RPG theme."""
        colors = self.get_palette()

        # Generate textures for backgrounds
        if TextureGenerator and get_cached_texture:
            parchment_texture = get_cached_texture(
                f"parchment_{self.current_theme.value}",
                TextureGenerator.generate_parchment_texture,
                200, 200,
                QColor(colors['bg_secondary'])
            )
            stone_texture = get_cached_texture(
                f"stone_{self.current_theme.value}",
                TextureGenerator.generate_stone_texture,
                200, 200,
                QColor(colors['bg_secondary'])
            )
            subtle_noise = get_cached_texture(
                "subtle_noise",
                TextureGenerator.generate_subtle_noise,
                100, 100, 8
            )
        else:
            parchment_texture = ""
            stone_texture = ""
            subtle_noise = ""

        stylesheet = f"""
        * {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
            border: none;
            font-family: "Spectral", "Georgia", serif;
        }}

        QMainWindow {{
            background-color: {colors['bg_primary']};
        }}

        QWidget {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
        }}

        /* Panels and GroupBoxes - Ornate medieval style */
        QGroupBox {{
            background-color: {colors['bg_secondary']};
            background-image: url({parchment_texture});
            background-repeat: repeat;
            color: {colors['text_primary']};
            border: 3px ridge {colors['border_ornate']};
            border-radius: 0px;
            margin-top: 18px;
            padding-top: 16px;
            padding-left: 12px;
            padding-right: 12px;
            padding-bottom: 12px;
            font-weight: 700;
            font-size: 11pt;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 16px;
            padding: 4px 12px;
            color: {colors['accent']};
            background-color: {colors['bg_primary']};
            border: 2px solid {colors['border_ornate']};
            border-radius: 0px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* Buttons - Ornate embossed style */
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['bg_tertiary']},
                stop:0.5 {colors['bg_secondary']},
                stop:1 {colors['bg_tertiary']});
            color: {colors['text_primary']};
            border: 2px outset {colors['border']};
            border-radius: 0px;
            padding: 8px 20px;
            font-weight: 600;
            font-size: 10pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            min-height: 32px;
            outline: none;
        }}

        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['accent_dark']},
                stop:0.5 {colors['accent']},
                stop:1 {colors['accent_dark']});
            border: 2px outset {colors['accent']};
            color: {colors['bg_primary']};
        }}

        QPushButton:pressed {{
            background-color: {colors['accent_dark']};
            border: 2px inset {colors['accent']};
            color: {colors['text_primary']};
            padding-top: 9px;
            padding-bottom: 7px;
        }}

        QPushButton:disabled {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_secondary']};
            border: 2px outset {colors['border']};
        }}

        /* Input Fields - Inset parchment style */
        QLineEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {colors['bg_primary']};
            background-image: url({subtle_noise});
            color: {colors['text_primary']};
            border: 2px inset {colors['border']};
            border-radius: 0px;
            padding: 6px 10px;
            selection-background-color: {colors['accent']};
            font-size: 11pt;
        }}

        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px inset {colors['accent']};
            outline: none;
            background-color: {colors['bg_secondary']};
        }}
        
        /* ComboBoxes - Fantasy dropdown style */
        QComboBox {{
            background-color: {colors['bg_secondary']};
            background-image: url({subtle_noise});
            color: {colors['text_primary']};
            border: 2px inset {colors['border']};
            border-radius: 0px;
            padding: 6px 10px;
            min-height: 32px;
            font-size: 11pt;
        }}

        QComboBox:hover {{
            border: 2px inset {colors['accent']};
        }}

        QComboBox:focus {{
            border: 2px inset {colors['accent']};
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            background-color: {colors['accent']};
            border-left: 2px solid {colors['border']};
            border-radius: 0px;
        }}

        QComboBox::drop-down:hover {{
            background-color: {colors['accent_hover']};
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors['bg_secondary']};
            background-image: url({parchment_texture});
            color: {colors['text_primary']};
            border: 3px ridge {colors['border_ornate']};
            border-radius: 0px;
            selection-background-color: {colors['accent']};
            padding: 4px;
        }}

        /* Tabs - Gothic arch style */
        QTabWidget {{
            background-color: {colors['bg_primary']};
            border: none;
        }}

        QTabBar::tab {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['bg_tertiary']},
                stop:1 {colors['bg_secondary']});
            color: {colors['text_primary']};
            border: 3px solid {colors['border']};
            border-bottom: none;
            padding: 10px 28px;
            margin-right: 2px;
            margin-top: 2px;
            border-radius: 0px;
            font-weight: 600;
            font-size: 10pt;
            text-transform: uppercase;
        }}

        QTabBar::tab:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['accent_dark']},
                stop:1 {colors['accent']});
            border: 3px solid {colors['accent']};
            color: {colors['bg_primary']};
        }}

        QTabBar::tab:selected {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['accent']},
                stop:1 {colors['accent_dark']});
            border: 3px solid {colors['accent']};
            border-bottom: none;
            color: {colors['bg_primary']};
            padding: 10px 28px;
        }}
        
        QTabBar::scroller {{
            width: 40px;
        }}
        
        /* Text Displays - Parchment style */
        QTextEdit, QPlainTextEdit {{
            background-color: {colors['bg_secondary']};
            background-image: url({parchment_texture});
            color: {colors['text_primary']};
            border: 2px inset {colors['border']};
            border-radius: 0px;
            padding: 10px;
            font-family: "Courier New", monospace;
            selection-background-color: {colors['accent']};
        }}

        QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px inset {colors['accent']};
        }}

        /* Scroll Bars - Medieval ornate */
        QScrollBar:vertical {{
            background-color: {colors['bg_secondary']};
            background-image: url({subtle_noise});
            width: 16px;
            border: 2px ridge {colors['border']};
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {colors['accent']};
            border: 2px outset {colors['accent_dark']};
            border-radius: 0px;
            min-height: 24px;
            margin: 2px 2px 2px 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {colors['accent_hover']};
        }}

        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
            border: none;
            width: 0px;
            height: 0px;
        }}

        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
            border: none;
            background: none;
        }}

        QScrollBar:horizontal {{
            background-color: {colors['bg_secondary']};
            background-image: url({subtle_noise});
            height: 16px;
            border: 2px ridge {colors['border']};
            margin: 0px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {colors['accent']};
            border: 2px outset {colors['accent_dark']};
            border-radius: 0px;
            min-width: 24px;
            margin: 2px 2px 2px 2px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {colors['accent_hover']};
        }}

        QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
            border: none;
            width: 0px;
            height: 0px;
        }}

        QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {{
            border: none;
            background: none;
        }}
        
        /* Labels */
        QLabel {{
            color: {colors['text_primary']};
            background-color: transparent;
        }}
        
        /* Checkboxes and Radio Buttons - Ornate style */
        QCheckBox, QRadioButton {{
            color: {colors['text_primary']};
            spacing: 6px;
            background-color: transparent;
        }}

        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
        }}

        QCheckBox::indicator:unchecked {{
            background-color: {colors['bg_primary']};
            border: 2px inset {colors['border']};
            border-radius: 0px;
        }}

        QCheckBox::indicator:unchecked:hover {{
            border: 2px inset {colors['accent']};
        }}

        QCheckBox::indicator:checked {{
            background-color: {colors['accent']};
            border: 2px outset {colors['accent_dark']};
            border-radius: 0px;
        }}

        QCheckBox::indicator:checked:hover {{
            background-color: {colors['accent_hover']};
            border: 2px outset {colors['accent']};
        }}

        /* Sliders - Medieval style */
        QSlider::groove:horizontal {{
            background-color: {colors['bg_secondary']};
            height: 8px;
            margin: 6px 0px;
            border-radius: 0px;
            border: 2px inset {colors['border']};
        }}

        QSlider::handle:horizontal {{
            background-color: {colors['accent']};
            width: 18px;
            margin: -5px 0px;
            border-radius: 0px;
            border: 2px outset {colors['accent_dark']};
        }}

        QSlider::handle:horizontal:hover {{
            background-color: {colors['accent_hover']};
            border: 2px outset {colors['accent']};
        }}
        
        /* Menu Bar and Menus */
        QMenuBar {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors['border']};
            padding: 2px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 12px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['bg_tertiary']};
            border-radius: 4px;
        }}
        
        QMenu {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 5px;
            padding: 4px 0px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors['accent']};
            color: {colors['bg_primary']};
            padding-left: 20px;
            padding-right: 20px;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {colors['border']};
            margin: 4px 0px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border-top: 1px solid {colors['border']};
        }}
        
        /* Table Widgets */
        QTableWidget {{
            background-color: {colors['bg_secondary']};
            gridline-color: {colors['border']};
        }}
        
        QTableWidget::item {{
            padding: 2px;
        }}
        
        QHeaderView::section {{
            background-color: {colors['bg_tertiary']};
            color: {colors['text_primary']};
            padding: 4px;
            border: none;
            border-right: 1px solid {colors['border']};
            border-bottom: 1px solid {colors['border']};
        }}
        
        /* Progress Bars - Game-style health/mana bars */
        QProgressBar {{
            background-color: {colors['bg_secondary']};
            border: 3px ridge {colors['border_ornate']};
            border-radius: 0px;
            text-align: center;
            height: 20px;
            font-size: 9pt;
            font-weight: bold;
            color: {colors['text_primary']};
        }}

        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['accent_hover']},
                stop:0.5 {colors['accent']},
                stop:1 {colors['accent_dark']});
            border-radius: 0px;
        }}
        
        /* Splitter handles */
        QSplitter::handle {{
            background-color: {colors['border']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 3px;
        }}
        
        QSplitter::handle:hover {{
            background-color: {colors['accent']};
        }}
        
        /* Scroll Area */
        QScrollArea {{
            background-color: {colors['bg_primary']};
            border: none;
        }}
        
        /* Header Bar - Ornate game banner */
        QWidget#headerBar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['bg_tertiary']},
                stop:1 {colors['bg_secondary']});
            background-image: url({stone_texture});
            border-bottom: 4px ridge {colors['border_ornate']};
            min-height: 60px;
            max-height: 60px;
        }}

        QLabel#headerTitle {{
            font-family: "Cinzel", "Crimson Text", "Georgia", serif;
            font-size: 20pt;
            font-weight: bold;
            color: {colors['accent']};
            background-color: transparent;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        /* Sidebar */
        QWidget#sidebar {{
            background-color: {colors['bg_primary']};
        }}

        QScrollArea#sidebarScroll {{
            background-color: {colors['bg_primary']};
            border-right: 3px ridge {colors['border']};
        }}

        /* Collapsible Section Header - Game-like menu */
        QPushButton#collapsibleHeader {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['accent_dark']},
                stop:0.5 {colors['accent']},
                stop:1 {colors['accent_dark']});
            color: {colors['bg_primary']};
            border: 3px outset {colors['border_ornate']};
            border-radius: 0px;
            padding: 10px 16px;
            font-weight: 700;
            font-size: 11pt;
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 1px;
            min-height: 32px;
        }}

        QPushButton#collapsibleHeader:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['accent_hover']},
                stop:0.5 {colors['accent']},
                stop:1 {colors['accent_hover']});
            border: 3px outset {colors['accent_hover']};
            color: {colors['bg_primary']};
        }}

        QPushButton#collapsibleHeader:checked {{
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        }}

        QWidget#collapsibleContent {{
            background-color: {colors['bg_secondary']};
            background-image: url({parchment_texture});
            border: 3px ridge {colors['border_ornate']};
            border-top: none;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        }}
        
        /* Theme toggle button - Ornate circular */
        QPushButton#themeToggle {{
            background-color: {colors['accent']};
            border: 3px outset {colors['border_ornate']};
            border-radius: 20px;
            padding: 4px;
            min-width: 40px;
            max-width: 40px;
            min-height: 40px;
            max-height: 40px;
        }}

        QPushButton#themeToggle:hover {{
            background-color: {colors['accent_hover']};
            border: 3px outset {colors['accent']};
        }}

        /* Toast notification - Game announcement style */
        QLabel#toast {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors['accent']},
                stop:1 {colors['accent_dark']});
            color: {colors['bg_primary']};
            padding: 12px 20px;
            border-radius: 0px;
            font-size: 11pt;
            font-weight: bold;
            text-transform: uppercase;
            border: 3px outset {colors['border_ornate']};
        }}
        
        /* Main canvas */
        QWidget#mainCanvas {{
            background-color: {colors['bg_primary']};
        }}
        
        /* Map container */
        QWidget#mapContainer {{
            background-color: {colors['bg_primary']};
        }}
        
        /* Log tabs (compact) */
        QTabWidget#logTabs {{
            background-color: {colors['bg_primary']};
        }}
        """
        
        return stylesheet
