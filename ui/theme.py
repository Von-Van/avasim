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
            font.setFamily("Segoe UI")
            font.setPointSize(size)
        elif style == "heading":
            font.setFamily("Segoe UI")
            font.setPointSize(size)
            font.setBold(True)
        elif style == "subheading":
            font.setFamily("Segoe UI")
            font.setPointSize(size)
            font.setWeight(600)
        elif style == "monospace":
            font.setFamily("Courier New")
            font.setPointSize(size)
            font.setStyleStrategy(QFont.PreferAntialias)
        elif style == "small":
            font.setFamily("Segoe UI")
            font.setPointSize(size)
        
        return font


class IconProvider:
    """Provides Font Awesome icons with theming support."""
    
    # Icon definitions for common UI elements
    ICONS = {
        "play": qta.icon("fa.play"),
        "pause": qta.icon("fa.pause"),
        "stop": qta.icon("fa.stop"),
        "settings": qta.icon("fa.cog"),
        "save": qta.icon("fa.save"),
        "load": qta.icon("fa.folder-open"),
        "export": qta.icon("fa.arrow-circle-o-up"),
        "add": qta.icon("fa.plus"),
        "delete": qta.icon("fa.trash-o"),
        "edit": qta.icon("fa.pencil"),
        "copy": qta.icon("fa.copy"),
        "undo": qta.icon("fa.undo"),
        "redo": qta.icon("fa.repeat"),
        "search": qta.icon("fa.search"),
        "refresh": qta.icon("fa.refresh"),
        "info": qta.icon("fa.info-circle"),
        "warning": qta.icon("fa.warning"),
        "error": qta.icon("fa.times-circle"),
        "success": qta.icon("fa.check-circle"),
        "arrow_up": qta.icon("fa.arrow-up"),
        "arrow_down": qta.icon("fa.arrow-down"),
        "arrow_left": qta.icon("fa.arrow-left"),
        "arrow_right": qta.icon("fa.arrow-right"),
        "menu": qta.icon("fa.bars"),
        "close": qta.icon("fa.times"),
        "star": qta.icon("fa.star"),
        "heart": qta.icon("fa.heart"),
        "shield": qta.icon("fa.shield"),
        "sword": qta.icon("fa.shield"),
        "person": qta.icon("fa.user"),
        "users": qta.icon("fa.users"),
        "map": qta.icon("fa.map"),
        "fire": qta.icon("fa.fire"),
        "zap": qta.icon("fa.bolt"),
    }
    
    @staticmethod
    def get_icon(name: str) -> QIcon:
        """Get an icon by name."""
        return IconProvider.ICONS.get(name, QIcon())


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
        """
        
        return stylesheet
