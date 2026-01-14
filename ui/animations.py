"""
Animation and feedback effects for AvaSim UI.
Provides smooth transitions, progress indicators, and visual feedback.
"""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QProgressBar, QLabel, QWidget
from PySide6.QtGui import QColor


class AnimatedButton:
    """Mixin to add animation effects to QPushButton widgets."""
    
    @staticmethod
    def setup_hover_animation(button):
        """Setup smooth color transition on hover."""
        button.animation = None
        original_stylesheet = button.styleSheet()
        
        def on_enter():
            if button.isEnabled():
                button.setCursor(button.cursor())
        
        def on_leave():
            if button.isEnabled():
                button.update()
        
        button.enterEvent = on_enter
        button.leaveEvent = on_leave


class ProgressIndicator(QProgressBar):
    """Custom progress indicator for combat simulation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setMaximum(100)
        self.setMinimum(0)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 24px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate)
        self.progress_value = 0
        
    def start_animation(self, duration_ms=2000):
        """Start a smooth animation."""
        self.setVisible(True)
        self.progress_value = 0
        self.setValue(0)
        self.animation_timer.start(30)
        
    def _animate(self):
        """Animate progress bar."""
        self.progress_value += 2
        self.setValue(min(self.progress_value, 90))  # Cap at 90% during animation
        
        if self.progress_value >= 90:
            self.animation_timer.stop()
    
    def complete(self):
        """Complete the animation."""
        self.animation_timer.stop()
        self.setValue(100)
        
        # Auto-hide after 500ms
        QTimer.singleShot(500, lambda: self.setVisible(False))


class TabTransitionHelper:
    """Helper for smooth tab transitions."""
    
    @staticmethod
    def setup_tab_animation(tab_widget):
        """Setup smooth tab switching transitions."""
        original_set_current = tab_widget.setCurrentIndex
        
        def animated_set_current(index):
            original_set_current(index)
            # The stylesheet handles the visual feedback
        
        tab_widget.setCurrentIndex = animated_set_current


class StatusBadge(QLabel):
    """Animated status badge for character states."""
    
    def __init__(self, text="", color="#6ba587", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 10pt;
            }}
        """)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._pulse)
        self.pulse_state = 0
    
    def start_pulse(self):
        """Start pulsing animation for attention."""
        self.animation_timer.start(200)
    
    def stop_pulse(self):
        """Stop pulsing animation."""
        self.animation_timer.stop()
        self.update()
    
    def _pulse(self):
        """Update pulse effect."""
        self.pulse_state = (self.pulse_state + 1) % 4
        opacity = 1.0 if self.pulse_state < 2 else 0.7
        # Visual pulse through opacity changes
        self.repaint()


class TextHighlighter:
    """Utility for syntax highlighting in log displays."""
    
    # Color codes for different log message types
    COLORS = {
        "critical": "#b22222",      # Red
        "hit": "#d2691e",           # Orange
        "miss": "#555555",          # Gray
        "move": "#1d6fb6",          # Blue
        "skill": "#2a9d8f",         # Teal
        "status": "#e76f51",        # Orange/brown
        "default": "#222222",       # Dark gray
    }
    
    @staticmethod
    def get_color_for_line(line: str) -> str:
        """Determine text color based on content."""
        low = line.lower()
        
        if any(word in low for word in ["critical", "crit"]):
            return TextHighlighter.COLORS["critical"]
        elif any(word in low for word in ["hit", "damage", "damage"]):
            return TextHighlighter.COLORS["hit"]
        elif any(word in low for word in ["miss", "fail", "graz", "evad"]):
            return TextHighlighter.COLORS["miss"]
        elif any(word in low for word in ["move", "position", "enter", "leave"]):
            return TextHighlighter.COLORS["move"]
        elif any(word in low for word in ["skill", "feat", "ability"]):
            return TextHighlighter.COLORS["skill"]
        elif any(word in low for word in ["status", "effect", "condition"]):
            return TextHighlighter.COLORS["status"]
        
        return TextHighlighter.COLORS["default"]
    
    @staticmethod
    def highlight_html(lines: list[str]) -> str:
        """Convert plain text lines to colored HTML."""
        import html
        
        html_lines = []
        for ln in lines:
            color = TextHighlighter.get_color_for_line(ln)
            safe = html.escape(ln)
            html_lines.append(f"<div style='color:{color}; margin-bottom:3px; line-height:1.4;'>{safe}</div>")
        
        return "".join(html_lines)


class IconButtonWithLabel(QWidget):
    """A button with an icon and optional label, with better spacing."""
    
    def __init__(self, button, label_text=None, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QHBoxLayout
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        layout.addWidget(button)
        
        if label_text:
            label = QLabel(label_text)
            label.setStyleSheet("margin: 0px; padding: 0px;")
            layout.addWidget(label)
        
        self.setLayout(layout)


class TooltipEnhancer:
    """Enhance tooltips with better styling."""
    
    @staticmethod
    def setup_tooltip(widget, text):
        """Setup a styled tooltip."""
        widget.setToolTip(text)
        # PySide6 handles tooltip styling through stylesheet
        widget.setToolTipDuration(3000)  # 3 second display
