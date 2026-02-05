"""
Enhanced map visualization widget for AvaSim.
Provides better graphics rendering and terrain visualization.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import Qt


class TacticalMapWidget(QGraphicsView):
    """Enhanced tactical map with professional graphics."""
    
    CELL_WIDTH = 32
    CELL_HEIGHT = 32
    
    # Terrain colors
    TERRAIN_COLORS = {
        "wall": QColor("#444444"),
        "forest": QColor("#2e8b57"),
        "water": QColor("#3a6ea5"),
        "mountain": QColor("#7f6f50"),
        "road": QColor("#c2a16a"),
        "normal": QColor("#f0ede6"),
    }
    
    # Highlight colors
    OCCUPANT_COLOR = QColor("#ffe8c2")      # Light yellow
    TARGET_COLOR = QColor("#ffd1d1")        # Light red
    ACTIVE_COLOR = QColor("#c8e6c9")        # Light green
    RANGE_OVERLAY = QColor(46, 125, 50, 90)  # Green overlay
    LOS_OVERLAY = QColor(30, 80, 160, 70)    # Blue overlay
    BLOCKED_OVERLAY = QColor(110, 110, 110, 80)  # Gray overlay
    PATH_OVERLAY = QColor(244, 162, 97, 120)     # Orange overlay
    
    def __init__(self, width=10, height=10, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.width = width
        self.height = height
        self.cells = {}
        self._on_click = None
        self._on_hover = None
        self._last_hover = None
        
        # Set scene rect
        self.scene.setSceneRect(0, 0, width * self.CELL_WIDTH, height * self.CELL_HEIGHT)
        
        # Rendering hints for smooth graphics
        self.setRenderHint(self.RenderHint.Antialiasing)
        self.setRenderHint(self.RenderHint.SmoothPixmapTransform)
        self.setMouseTracking(True)
        
        # Initialize grid
        self._draw_empty_grid()
    
    def _draw_empty_grid(self):
        """Draw an empty tactical grid."""
        self.scene.clear()
        self.cells = {}
        
        grid_pen = QPen(QColor("#999999"))
        grid_pen.setWidth(1)
        
        for y in range(self.height):
            for x in range(self.width):
                rect_x = x * self.CELL_WIDTH
                rect_y = y * self.CELL_HEIGHT
                
                # Draw cell background
                brush = QBrush(self.TERRAIN_COLORS["normal"])
                rect_item = self.scene.addRect(
                    rect_x, rect_y,
                    self.CELL_WIDTH - 1, self.CELL_HEIGHT - 1,
                    grid_pen, brush
                )
                
                self.cells[(x, y)] = {
                    "rect": rect_item,
                    "text": None,
                    "terrain": "normal",
                    "occupant": None,
                }
    
    def draw_snapshot(self, snapshot):
        """Draw a snapshot of the combat state."""
        if not snapshot:
            self._draw_empty_grid()
            return
        
        self.scene.clear()
        self.cells = {}
        
        grid_pen = QPen(QColor("#999999"))
        grid_pen.setWidth(1)
        
        cells = snapshot.get("cells", [])
        actor_pos = snapshot.get("actor", {}).get("position")
        target_pos = snapshot.get("target", {}).get("position")
        overlays = snapshot.get("overlays", {})
        path = snapshot.get("path", [])
        
        # Draw all cells
        for cell in cells:
            x = cell.get("x", 0)
            y = cell.get("y", 0)
            terrain = cell.get("terrain", "normal")
            occupant = cell.get("occupant")
            
            rect_x = x * self.CELL_WIDTH
            rect_y = y * self.CELL_HEIGHT
            
            # Determine color
            color = self.TERRAIN_COLORS.get(terrain, self.TERRAIN_COLORS["normal"])
            
            if (x, y) == actor_pos:
                color = self.ACTIVE_COLOR
            elif (x, y) == target_pos:
                color = self.TARGET_COLOR
            elif occupant:
                color = self.OCCUPANT_COLOR
            
            brush = QBrush(color)
            rect_item = self.scene.addRect(
                rect_x, rect_y,
                self.CELL_WIDTH - 1, self.CELL_HEIGHT - 1,
                grid_pen, brush
            )
            tooltip_parts = [f"({x}, {y})", f"Terrain: {terrain}"]
            
            # Add occupant text if present
            text_item = None
            if occupant:
                text_item = self.scene.addText(str(occupant)[:2])
                text_item.setDefaultTextColor(QColor("#111111"))
                text_item.setPos(rect_x + 8, rect_y + 4)
                font = text_item.font()
                font.setPointSize(9)
                font.setBold(True)
                text_item.setFont(font)
                tooltip_parts.append(f"Occupant: {occupant}")
            rect_item.setToolTip(" | ".join(tooltip_parts))
            
            self.cells[(x, y)] = {
                "rect": rect_item,
                "text": text_item,
                "terrain": terrain,
                "occupant": occupant,
            }
        
        self._apply_overlays(overlays, path)

        # Fit to view
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_interaction_handlers(self, on_click=None, on_hover=None):
        """Set callbacks for cell interactions."""
        self.on_cell_clicked = on_click
        self.on_cell_hover = on_hover

    def draw_map_state(self, cells, actor_pos=None, target_pos=None, overlays=None, path=None):
        """Draw a tactical map state from a cells list."""
        snapshot = {
            "cells": cells or [],
            "actor": {"position": actor_pos},
            "target": {"position": target_pos},
            "overlays": overlays or {},
            "path": path or [],
        }
        self.draw_snapshot(snapshot)
    
    def highlight_position(self, x: int, y: int, color_name: str = "target"):
        """Highlight a specific cell."""
        if (x, y) not in self.cells:
            return
        
        color_map = {
            "active": self.ACTIVE_COLOR,
            "target": self.TARGET_COLOR,
            "occupant": self.OCCUPANT_COLOR,
        }
        
        color = color_map.get(color_name, self.TARGET_COLOR)
        self.cells[(x, y)]["rect"].setBrush(QBrush(color))

    def _apply_overlays(self, overlays: dict, path: list):
        if overlays:
            for kind, cells in overlays.items():
                if not cells:
                    continue
                if kind == "range":
                    color = self.RANGE_OVERLAY
                elif kind == "los":
                    color = self.LOS_OVERLAY
                elif kind == "blocked":
                    color = self.BLOCKED_OVERLAY
                else:
                    color = self.RANGE_OVERLAY
                for x, y in cells:
                    if (x, y) not in self.cells:
                        continue
                    rect = self.scene.addRect(
                        x * self.CELL_WIDTH, y * self.CELL_HEIGHT,
                        self.CELL_WIDTH - 1, self.CELL_HEIGHT - 1,
                        QPen(Qt.NoPen), QBrush(color),
                    )
                    rect.setZValue(2)
        if path:
            for idx, (x, y) in enumerate(path):
                if (x, y) not in self.cells:
                    continue
                rect = self.scene.addRect(
                    x * self.CELL_WIDTH, y * self.CELL_HEIGHT,
                    self.CELL_WIDTH - 1, self.CELL_HEIGHT - 1,
                    QPen(Qt.NoPen), QBrush(self.PATH_OVERLAY),
                )
                rect.setZValue(3)
                if idx > 0:
                    px, py = path[idx - 1]
                    arrow = ""
                    if x > px:
                        arrow = ">"
                    elif x < px:
                        arrow = "<"
                    elif y > py:
                        arrow = "v"
                    elif y < py:
                        arrow = "^"
                    if arrow:
                        text_item = self.scene.addText(arrow)
                        text_item.setDefaultTextColor(QColor("#333333"))
                        text_item.setPos(x * self.CELL_WIDTH + 12, y * self.CELL_HEIGHT + 6)
                        text_item.setZValue(4)
    
    def set_grid_dimensions(self, width: int, height: int):
        """Change grid dimensions."""
        self.width = width
        self.height = height
        self.scene.setSceneRect(0, 0, width * self.CELL_WIDTH, height * self.CELL_HEIGHT)
        self._draw_empty_grid()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            cell = self._event_to_cell(event)
            if cell and callable(self.on_cell_clicked):
                self.on_cell_clicked(*cell)
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        cell = self._event_to_cell(event)
        if cell != self._last_hover:
            self._last_hover = cell
            if cell and callable(self.on_cell_hover):
                self.on_cell_hover(*cell)
        return super().mouseMoveEvent(event)

    def _event_to_cell(self, event):
        scene_pos = self.mapToScene(event.pos())
        x = int(scene_pos.x() // self.CELL_WIDTH)
        y = int(scene_pos.y() // self.CELL_HEIGHT)
        if 0 <= x < self.width and 0 <= y < self.height:
            return (x, y)
        return None

class MapLegend(QWidget):
    """A legend for the tactical map."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        self.legend_items = []
        
        self._add_legend_item("Initials", "Active unit identifier")
        self._add_legend_item("Yellow cell", "Current position")
        self._add_legend_item("Red cell", "Target position")
        self._add_legend_item("Light cell", "Empty space")
        
        self.setLayout(layout)
    
    def _add_legend_item(self, symbol: str, description: str):
        """Add a legend entry."""
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(8)
        
        symbol_label = QLabel(f"• {symbol}")
        symbol_label.setStyleSheet("font-weight: bold;")
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: gray;")
        
        item_layout.addWidget(symbol_label)
        item_layout.addWidget(desc_label)
        item_layout.addStretch()
        
        self.layout().addLayout(item_layout)

