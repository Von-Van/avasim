"""
Professional theming and styling system for AvaSim UI.
Provides centralized color management, icons, and QSS stylesheet generation.
"""

from enum import Enum
from typing import Dict, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import QApplication, QStyle
import qtawesome as qta


class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"


class ColorPalette:
    """Centralized color definitions for consistent theming."""
    
    # Dark theme colors
    DARK = {
        "bg_primary": "#1e1b18",      # Main background
        "bg_secondary": "#26221f",    # Panel/card background
        "bg_tertiary": "#2e2a25",     # Hover/selected state
        "text_primary": "#f0ede6",    # Main text
        "text_secondary": "#b8b3aa",  # Dimmed text
        "accent": "#d6a756",          # Primary accent (golden)
        "accent_hover": "#e8bf6d",    # Accent hover state
        "accent_dark": "#c1842f",     # Darker accent
        "border": "#3d3630",          # Border color
        "success": "#6ba587",         # Success state (green)
        "warning": "#d2691e",         # Warning state (orange)
        "error": "#b22222",           # Error state (red)
        "info": "#1d6fb6",            # Info state (blue)
    }
    
    # Light theme colors
    LIGHT = {
        "bg_primary": "#f4efe7",      # Main background
        "bg_secondary": "#ffffff",    # Panel/card background
        "bg_tertiary": "#e8e1d9",     # Hover/selected state
        "text_primary": "#1f1a17",    # Main text
        "text_secondary": "#6b6560",  # Dimmed text
        "accent": "#c1842f",          # Primary accent (darker tan)
        "accent_hover": "#d6a756",    # Accent hover state
        "accent_dark": "#8b5a00",     # Darker accent
        "border": "#d4cfc5",          # Border color
        "success": "#4a8f6e",         # Success state (green)
        "warning": "#d2691e",         # Warning state (orange)
        "error": "#b22222",           # Error state (red)
        "info": "#1d6fb6",            # Info state (blue)
    }


class FontConfig:
    """Font configurations for different UI elements."""
    
    @staticmethod
    def get_font(style: str, size: int = 11) -> QFont:
        """Get a configured font for specific UI style."""
        font = QFont()
        
        if style == "default":
            font.setFamilies(["Inter", "SF Pro Display", "Segoe UI", "Helvetica Neue"])
            font.setPointSize(size)
        elif style == "heading":
            font.setFamilies(["Inter", "SF Pro Display", "Segoe UI", "Helvetica Neue"])
            font.setPointSize(size)
            font.setBold(True)
        elif style == "subheading":
            font.setFamilies(["Inter", "SF Pro Display", "Segoe UI", "Helvetica Neue"])
            font.setPointSize(size)
            font.setWeight(600)
        elif style == "monospace":
            font.setFamilies(["JetBrains Mono", "Cascadia Code", "SF Mono", "Courier New"])
            font.setPointSize(size)
            font.setStyleStrategy(QFont.PreferAntialias)
        elif style == "small":
            font.setFamilies(["Inter", "SF Pro Display", "Segoe UI", "Helvetica Neue"])
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
        """Generate QSS stylesheet for current theme."""
        colors = self.get_palette()
        
        stylesheet = f"""
        * {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
            border: none;
        }}
        
        QMainWindow {{
            background-color: {colors['bg_primary']};
        }}
        
        QWidget {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
        }}
        
        /* Panels and GroupBoxes - with subtle depth */
        QGroupBox {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            padding-left: 8px;
            padding-right: 8px;
            padding-bottom: 8px;
            font-weight: 600;
            font-size: 11pt;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0px 6px;
            color: {colors['accent']};
        }}
        
        /* Buttons - improved styling with better hover states */
        QPushButton {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 7px 18px;
            font-weight: 500;
            font-size: 11pt;
            min-height: 32px;
            outline: none;
        }}
        
        QPushButton:hover {{
            background-color: {colors['bg_tertiary']};
            border: 1px solid {colors['accent']};
            color: {colors['accent_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent']};
            color: {colors['bg_primary']};
            border: 1px solid {colors['accent_dark']};
        }}
        
        QPushButton:disabled {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_secondary']};
            border: 1px solid {colors['text_secondary']};
        }}
        
        /* Input Fields - with focus states */
        QLineEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 5px;
            padding: 6px 10px;
            selection-background-color: {colors['accent']};
            font-size: 11pt;
        }}
        
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {colors['accent']};
            outline: none;
        }}
        
        /* ComboBoxes */
        QComboBox {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 5px;
            padding: 6px 10px;
            min-height: 32px;
            font-size: 11pt;
        }}
        
        QComboBox:hover {{
            border: 1px solid {colors['accent']};
        }}
        
        QComboBox:focus {{
            border: 2px solid {colors['accent']};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            background-color: {colors['accent']};
            border-left: 1px solid {colors['border']};
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }}
        
        QComboBox::drop-down:hover {{
            background-color: {colors['accent_hover']};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            selection-background-color: {colors['accent']};
            padding: 4px;
        }}
        
        /* Tabs - improved styling */
        QTabWidget {{
            background-color: {colors['bg_primary']};
            border: none;
        }}
        
        QTabBar::tab {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-bottom: none;
            padding: 8px 24px;
            margin-right: 2px;
            margin-top: 2px;
            border-radius: 6px 6px 0px 0px;
            font-weight: 500;
            font-size: 11pt;
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors['bg_tertiary']};
            border: 1px solid {colors['accent']};
            color: {colors['accent_hover']};
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['bg_secondary']};
            border: 2px solid {colors['accent']};
            border-bottom: none;
            color: {colors['accent']};
            padding: 7px 24px;
        }}
        
        QTabBar::scroller {{
            width: 40px;
        }}
        
        /* Text Displays */
        QTextEdit, QPlainTextEdit {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 5px;
            padding: 10px;
            font-family: "Courier New";
            selection-background-color: {colors['accent']};
        }}
        
        QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {colors['accent']};
        }}
        
        /* Scroll Bars - styled */
        QScrollBar:vertical {{
            background-color: {colors['bg_primary']};
            width: 14px;
            border: none;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['accent']};
            border-radius: 7px;
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
            background-color: {colors['bg_primary']};
            height: 14px;
            border: none;
            margin: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors['accent']};
            border-radius: 7px;
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
        
        /* Checkboxes and Radio Buttons */
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
            background-color: {colors['bg_secondary']};
            border: 2px solid {colors['border']};
            border-radius: 3px;
        }}
        
        QCheckBox::indicator:unchecked:hover {{
            border: 2px solid {colors['accent']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors['accent']};
            border: 2px solid {colors['accent']};
            border-radius: 3px;
        }}
        
        QCheckBox::indicator:checked:hover {{
            background-color: {colors['accent_hover']};
            border: 2px solid {colors['accent_hover']};
        }}
        
        /* Sliders */
        QSlider::groove:horizontal {{
            background-color: {colors['bg_secondary']};
            height: 8px;
            margin: 6px 0px;
            border-radius: 4px;
            border: 1px solid {colors['border']};
        }}
        
        QSlider::handle:horizontal {{
            background-color: {colors['accent']};
            width: 18px;
            margin: -5px 0px;
            border-radius: 9px;
            border: 1px solid {colors['accent_dark']};
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {colors['accent_hover']};
            border: 1px solid {colors['accent']};
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
        
        /* Progress Bars */
        QProgressBar {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            text-align: center;
            height: 16px;
            font-size: 9pt;
            color: {colors['text_primary']};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['accent']};
            border-radius: 3px;
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
        
        /* Header Bar */
        QWidget#headerBar {{
            background-color: {colors['bg_secondary']};
            border-bottom: 2px solid {colors['accent']};
            min-height: 44px;
            max-height: 44px;
        }}
        
        QLabel#headerTitle {{
            font-size: 16pt;
            font-weight: bold;
            color: {colors['accent']};
            background-color: transparent;
        }}
        
        /* Sidebar */
        QWidget#sidebar {{
            background-color: {colors['bg_primary']};
        }}
        
        QScrollArea#sidebarScroll {{
            background-color: {colors['bg_primary']};
            border-right: 1px solid {colors['border']};
        }}
        
        /* Collapsible Section Header */
        QPushButton#collapsibleHeader {{
            background-color: {colors['bg_tertiary']};
            color: {colors['accent']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: 700;
            font-size: 11pt;
            text-align: left;
            min-height: 28px;
        }}
        
        QPushButton#collapsibleHeader:hover {{
            background-color: {colors['accent']};
            color: {colors['bg_primary']};
        }}
        
        QPushButton#collapsibleHeader:checked {{
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        }}
        
        QWidget#collapsibleContent {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border']};
            border-top: none;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
        }}
        
        /* Theme toggle button */
        QPushButton#themeToggle {{
            background-color: transparent;
            border: 1px solid {colors['border']};
            border-radius: 18px;
            padding: 4px;
            min-width: 36px;
            max-width: 36px;
            min-height: 36px;
            max-height: 36px;
        }}
        
        QPushButton#themeToggle:hover {{
            background-color: {colors['bg_tertiary']};
            border: 1px solid {colors['accent']};
        }}
        
        /* Toast notification */
        QLabel#toast {{
            background-color: {colors['bg_tertiary']};
            color: {colors['text_primary']};
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 10pt;
            border: 1px solid {colors['accent']};
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
