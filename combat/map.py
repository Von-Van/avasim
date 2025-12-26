from dataclasses import dataclass
from typing import Optional, Any, List, Tuple, Dict, Set
from collections import deque
from heapq import heappush, heappop
from .enums import TerrainType

@dataclass
class Tile:
    x: int
    y: int
    terrain_type: TerrainType = TerrainType.NORMAL
    passable: bool = True
    move_cost: int = 1
    height: int = 0
    occupant: Optional[Any] = None

    def can_enter(self, unit: Optional[Any] = None) -> bool:
        if not self.passable:
            return False
        if self.occupant is not None:
            return False
        return True

    def __repr__(self) -> str:
        return f"Tile({self.x},{self.y},{self.terrain_type.value})"

class TacticalMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: List[List[Tile]] = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(Tile(x=x, y=y))
            self.grid.append(row)

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def is_passable(self, x: int, y: int, unit: Optional[Any] = None) -> bool:
        tile = self.get_tile(x, y)
        if tile is None:
            return False
        return tile.can_enter(unit)

    def get_neighbors(self, x: int, y: int, allow_diagonal: bool = False) -> List[Tuple[int, int]]:
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny))
        if allow_diagonal:
            for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append((nx, ny))
        return neighbors

    def manhattan_distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        return abs(x2 - x1) + abs(y2 - y1)

    def get_reachable_tiles(self, start_x: int, start_y: int, movement_points: int, unit: Optional[Any] = None) -> Dict[Tuple[int, int], int]:
        reachable = {(start_x, start_y): 0}
        queue = deque([(start_x, start_y, 0)])
        while queue:
            x, y, cost = queue.popleft()
            for nx, ny in self.get_neighbors(x, y):
                tile = self.get_tile(nx, ny)
                if tile is None or not tile.can_enter(unit):
                    continue
                new_cost = cost + tile.move_cost
                if new_cost > movement_points:
                    continue
                if (nx, ny) in reachable and reachable[(nx, ny)] <= new_cost:
                    continue
                reachable[(nx, ny)] = new_cost
                queue.append((nx, ny, new_cost))
        return reachable

    def find_path(self, start_x: int, start_y: int, goal_x: int, goal_y: int, unit: Optional[Any] = None) -> Optional[List[Tuple[int, int]]]:
        if not self.is_passable(goal_x, goal_y, unit):
            return None
        counter = 0
        start_node = (0, counter, start_x, start_y, [(start_x, start_y)])
        frontier = [start_node]
        visited: Set[Tuple[int, int]] = set()
        while frontier:
            _, _, x, y, path = heappop(frontier)
            if (x, y) in visited:
                continue
            visited.add((x, y))
            if x == goal_x and y == goal_y:
                return path
            for nx, ny in self.get_neighbors(x, y):
                if (nx, ny) in visited:
                    continue
                tile = self.get_tile(nx, ny)
                if tile is None or not tile.can_enter(unit):
                    continue
                g_cost = len(path)
                h_cost = self.manhattan_distance(nx, ny, goal_x, goal_y)
                f_cost = g_cost + h_cost
                new_path = path + [(nx, ny)]
                counter += 1
                heappush(frontier, (f_cost, counter, nx, ny, new_path))
        return None

    def get_tiles_in_range(self, center_x: int, center_y: int, min_range: int = 0, max_range: int = 1) -> List[Tuple[int, int]]:
        tiles = []
        for y in range(max(0, center_y - max_range), min(self.height, center_y + max_range + 1)):
            for x in range(max(0, center_x - max_range), min(self.width, center_x + max_range + 1)):
                dist = self.manhattan_distance(center_x, center_y, x, y)
                if min_range <= dist <= max_range:
                    tiles.append((x, y))
        return tiles

    def has_line_of_sight(self, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        x0, y0 = a
        x1, y1 = b
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if (x0, y0) not in (a, b):
                tile = self.get_tile(x0, y0)
                if tile and tile.terrain_type == TerrainType.WALL:
                    return False
            if (x0, y0) == (x1, y1):
                return True
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def cover_between(self, attacker: Tuple[int, int], defender: Tuple[int, int]) -> str:
        if not self.has_line_of_sight(attacker, defender):
            return "full"
        tx, ty = defender
        tile = self.get_tile(tx, ty)
        if tile and tile.terrain_type == TerrainType.FOREST:
            return "half"
        return "none"

    def set_occupant(self, x: int, y: int, occupant: Optional[Any]):
        tile = self.get_tile(x, y)
        if tile:
            tile.occupant = occupant

    def clear_occupant(self, x: int, y: int):
        self.set_occupant(x, y, None)
