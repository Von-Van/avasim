"""
Reusable UI components for AvaSim.
Provides commonly used widgets to reduce duplication.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QWidget
)
from PySide6.QtCore import Qt
from ui_theme import IconProvider


class LabeledComboBox(QWidget):
    """A label paired with a combo box."""
    
    def __init__(self, label_text: str, items: list[str] = None, 
                 tooltip: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setMinimumWidth(100)
        
        self.combo = QComboBox()
        if items:
            self.combo.addItems(items)
        if tooltip:
            self.combo.setToolTip(tooltip)
        self.combo.setMinimumWidth(120)
        
        layout.addWidget(label)
        layout.addWidget(self.combo)
        layout.addStretch()
        
        self.setLayout(layout)


class LabeledSpinBox(QWidget):
    """A label paired with a spin box."""
    
    def __init__(self, label_text: str, min_val: int = 0, max_val: int = 100,
                 value: int = 0, tooltip: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        label = QLabel(label_text)
        
        self.spinbox = QSpinBox()
        self.spinbox.setRange(min_val, max_val)
        self.spinbox.setValue(value)
        if tooltip:
            self.spinbox.setToolTip(tooltip)
        self.spinbox.setMaximumWidth(70)
        
        layout.addWidget(label)
        layout.addWidget(self.spinbox)
        layout.addStretch()
        
        self.setLayout(layout)


class LabeledLineEdit(QWidget):
    """A label paired with a line edit."""
    
    def __init__(self, label_text: str, placeholder: str = "",
                 tooltip: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setMinimumWidth(100)
        
        self.input = QLineEdit()
        if placeholder:
            self.input.setPlaceholderText(placeholder)
        if tooltip:
            self.input.setToolTip(tooltip)
        
        layout.addWidget(label)
        layout.addWidget(self.input)
        
        self.setLayout(layout)


class IconButton(QPushButton):
    """A button with an icon and optional text."""
    
    def __init__(self, icon_name: str, text: str = "", tooltip: str = "", parent=None):
        super().__init__(text, parent)
        icon = IconProvider.get_icon(icon_name)
        self.setIcon(icon)
        if tooltip:
            self.setToolTip(tooltip)
        self.setMinimumHeight(32)
        if text:
            self.setMinimumWidth(140)


class SectionGroupBox(QGroupBox):
    """A styled group box for organizing UI sections."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
        self.setLayout(layout)
    
    def add_row_layout(self):
        """Add a horizontal row to the group."""
        row = QHBoxLayout()
        row.setSpacing(12)
        self.layout().addLayout(row)
        return row
    
    def add_widget(self, widget):
        """Add a widget to the group."""
        self.layout().addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to the group."""
        self.layout().addLayout(layout)


class ControlRow(QWidget):
    """A horizontal row of controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.setLayout(layout)
    
    def add_label(self, text: str) -> QLabel:
        """Add a label."""
        label = QLabel(text)
        self.layout().addWidget(label)
        return label
    
    def add_widget(self, widget):
        """Add a widget."""
        self.layout().addWidget(widget)
        return widget
    
    def add_stretch(self):
        """Add stretch space."""
        self.layout().addStretch()
    
    def add_spacing(self, space: int = 20):
        """Add fixed spacing."""
        self.layout().addSpacing(space)
