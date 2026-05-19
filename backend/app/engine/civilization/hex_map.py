"""Hex coordinate math library using axial coordinates for Civilization: A New Dawn."""

from collections import deque
from typing import Callable

AXIAL_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

TERRAIN_DIFFICULTY = {
    "grassland": 1,
    "hills": 2,
    "forest": 3,
    "desert": 4,
    "mountain": 5,
    "water": 1,
    "natural_wonder": 5,
}


def hex_neighbors(q: int, r: int) -> list[tuple[int, int]]:
    """Return the 6 axial neighbors of hex (q, r)."""
    return [(q + dq, r + dr) for dq, dr in AXIAL_DIRECTIONS]


def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """Manhattan distance between two hexes in axial coordinates.
    Formula: max(|q1-q2|, |r1-r2|, |q1+r1-q2-r2|)"""
    return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2)))


def hex_ring(center_q: int, center_r: int, radius: int) -> list[tuple[int, int]]:
    """All hexes at exactly `radius` distance from center. Ring of radius 0 = [center]."""
    if radius == 0:
        return [(center_q, center_r)]

    results = []
    # Start at the hex `radius` steps in direction 4 (-1, 1) from center
    q = center_q + AXIAL_DIRECTIONS[4][0] * radius
    r = center_r + AXIAL_DIRECTIONS[4][1] * radius

    for i in range(6):
        for _ in range(radius):
            results.append((q, r))
            q += AXIAL_DIRECTIONS[i][0]
            r += AXIAL_DIRECTIONS[i][1]

    return results


def hex_reachable(
    start: tuple[int, int],
    max_dist: int,
    passable: Callable[[tuple[int, int]], bool],
) -> set[tuple[int, int]]:
    """BFS from start, returning all hexes reachable within max_dist steps.
    Only steps through hexes where passable(hex) returns True.
    The start hex is always included."""
    visited: set[tuple[int, int]] = {start}
    fringes: deque[tuple[tuple[int, int], int]] = deque()
    fringes.append((start, 0))

    while fringes:
        current, dist = fringes.popleft()
        if dist >= max_dist:
            continue
        for neighbor in hex_neighbors(*current):
            if neighbor not in visited and passable(neighbor):
                visited.add(neighbor)
                fringes.append((neighbor, dist + 1))

    return visited


def connected_components(coords: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    """Return connected components of hex coordinates. Two hexes connect if they are axial neighbors."""
    visited: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []

    for coord in coords:
        if coord in visited:
            continue
        component: set[tuple[int, int]] = set()
        queue = deque([coord])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            component.add(current)
            for neighbor in hex_neighbors(*current):
                if neighbor in coords and neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)

    return components


def terrain_difficulty(terrain: str) -> int:
    """Return difficulty level for a terrain type. Unknown terrain defaults to 5."""
    return TERRAIN_DIFFICULTY.get(terrain, 5)
