"""Tests for hex coordinate math library."""

import pytest

from app.engine.civilization.hex_map import (
    TERRAIN_DIFFICULTY,
    hex_distance,
    hex_neighbors,
    hex_reachable,
    hex_ring,
    terrain_difficulty,
)


# --- hex_neighbors ---


class TestHexNeighbors:
    def test_always_returns_six(self):
        assert len(hex_neighbors(0, 0)) == 6
        assert len(hex_neighbors(3, -2)) == 6
        assert len(hex_neighbors(-5, 10)) == 6

    def test_origin_neighbors(self):
        expected = {(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)}
        assert set(hex_neighbors(0, 0)) == expected

    def test_non_origin_neighbors(self):
        # Neighbors of (2, -1)
        expected = {(3, -1), (3, -2), (2, -2), (1, -1), (1, 0), (2, 0)}
        assert set(hex_neighbors(2, -1)) == expected

    def test_no_duplicates(self):
        result = hex_neighbors(0, 0)
        assert len(result) == len(set(result))


# --- hex_distance ---


class TestHexDistance:
    def test_symmetric(self):
        assert hex_distance(0, 0, 3, -2) == hex_distance(3, -2, 0, 0)
        assert hex_distance(1, 2, -3, 4) == hex_distance(-3, 4, 1, 2)

    def test_adjacent(self):
        assert hex_distance(0, 0, 1, 0) == 1

    def test_two_steps(self):
        assert hex_distance(0, 0, 2, -1) == 2

    def test_same_hex(self):
        assert hex_distance(0, 0, 0, 0) == 0
        assert hex_distance(5, -3, 5, -3) == 0

    def test_larger_distance(self):
        # (0,0) to (3,0) = 3
        assert hex_distance(0, 0, 3, 0) == 3


# --- hex_ring ---


class TestHexRing:
    def test_radius_zero(self):
        result = hex_ring(0, 0, 0)
        assert result == [(0, 0)]

    def test_radius_one_count(self):
        result = hex_ring(0, 0, 1)
        assert len(result) == 6

    def test_radius_one_all_adjacent(self):
        result = hex_ring(0, 0, 1)
        for q, r in result:
            assert hex_distance(0, 0, q, r) == 1

    def test_radius_two_count(self):
        result = hex_ring(0, 0, 2)
        assert len(result) == 12

    def test_radius_two_all_at_distance_two(self):
        result = hex_ring(0, 0, 2)
        for q, r in result:
            assert hex_distance(0, 0, q, r) == 2

    def test_no_duplicates(self):
        result = hex_ring(0, 0, 3)
        assert len(result) == len(set(result))

    def test_non_origin_center(self):
        center = (2, -1)
        result = hex_ring(*center, 1)
        assert len(result) == 6
        for q, r in result:
            assert hex_distance(*center, q, r) == 1


# --- hex_reachable ---


class TestHexReachable:
    def test_max_dist_zero(self):
        result = hex_reachable((0, 0), 0, lambda h: True)
        assert result == {(0, 0)}

    def test_max_dist_one_all_passable(self):
        result = hex_reachable((0, 0), 1, lambda h: True)
        assert len(result) == 7  # center + 6 neighbors
        assert (0, 0) in result

    def test_blocker_excludes_hex_and_behind(self):
        # Block (1, 0). Hex (2, 0) is behind it and should be unreachable
        # at max_dist=2 since BFS must pass through (1, 0).
        blocked = {(1, 0)}

        def passable(h):
            return h not in blocked

        result = hex_reachable((0, 0), 2, passable)
        assert (1, 0) not in result
        assert (2, 0) not in result  # only reachable via (1, 0) in 2 steps along q axis

    def test_start_always_included(self):
        # Even if passable returns False for start, it should still be included
        result = hex_reachable((0, 0), 1, lambda h: False)
        assert (0, 0) in result

    def test_all_passable_dist_two(self):
        result = hex_reachable((0, 0), 2, lambda h: True)
        # center (1) + ring1 (6) + ring2 (12) = 19
        assert len(result) == 19


# --- terrain_difficulty ---


class TestTerrainDifficulty:
    @pytest.mark.parametrize("terrain,expected", list(TERRAIN_DIFFICULTY.items()))
    def test_known_terrains(self, terrain, expected):
        assert terrain_difficulty(terrain) == expected

    def test_unknown_terrain_defaults_to_five(self):
        assert terrain_difficulty("swamp") == 5
        assert terrain_difficulty("") == 5
        assert terrain_difficulty("lava") == 5
