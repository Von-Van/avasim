"""
Enhanced map visualization widget for AvaSim.
Provides better graphics rendering and terrain visualization.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout
from PySide6.QtGui import QPen, QBrush, QColor, QFont
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
    
    def __init__(self, width=10, height=10, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.width = width
        self.height = height
        self.cells = {}
        
        # Set scene rect
        self.scene.setSceneRect(0, 0, width * self.CELL_WIDTH, height * self.CELL_HEIGHT)
        
        # Rendering hints for smooth graphics
        self.setRenderHint(self.RenderHint.Antialiasing)
        self.setRenderHint(self.RenderHint.SmoothPixmapTransform)
        
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
            
            self.cells[(x, y)] = {
                "rect": rect_item,
                "text": text_item,
                "terrain": terrain,
                "occupant": occupant,
            }
        
        # Fit to view
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
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
    
    def set_grid_dimensions(self, width: int, height: int):
        """Change grid dimensions."""
        self.width = width
        self.height = height
        self.scene.setSceneRect(0, 0, width * self.CELL_WIDTH, height * self.CELL_HEIGHT)
        self._draw_empty_grid()


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


from PySide6.QtWidgets import QLabel
