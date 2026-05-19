"""Tests for the Civilization: A New Dawn v2 heuristic evaluator."""

import pytest

from app.engine.civilization.state import (
    Army,
    Caravan,
    City,
    CivGameState,
    ControlToken,
    FocusCard,
    HexCoord,
    MapTile,
    PlayerState,
    VictoryCard,
)
from app.engine.civilization.evaluator import (
    evaluate_position,
    score_cities,
    score_diplomacy,
    score_districts,
    score_economy,
    score_focus_row,
    score_forts,
    score_military,
    score_position,
    score_resources,
    score_tech,
    score_territory,
    score_victory_progress,
    score_wonders,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_map() -> dict[tuple[int, int], MapTile]:
    tiles: dict[tuple[int, int], MapTile] = {}
    coords = [(0, 0), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
    for q, r in coords:
        tiles[(q, r)] = MapTile(coord=HexCoord(q, r), terrain="grassland")
    return tiles


def _resource_map() -> dict[tuple[int, int], MapTile]:
    tiles = _empty_map()
    tiles[(1, 0)] = MapTile(
        coord=HexCoord(1, 0), terrain="grassland",
        has_resource="marble",
    )
    tiles[(0, 1)] = MapTile(
        coord=HexCoord(0, 1), terrain="hills",
        has_natural_wonder="Great Barrier Reef",
    )
    return tiles


def _minimal_player(pid: int = 1, **overrides) -> PlayerState:
    defaults = dict(player_id=pid, leader="Trajan")
    defaults.update(overrides)
    return PlayerState(**defaults)


def _game(players, map_tiles=None, **kw) -> CivGameState:
    if map_tiles is None:
        map_tiles = _empty_map()
    return CivGameState(
        map_tiles=map_tiles,
        players=tuple(players),
        current_player=players[0].player_id,
        **kw,
    )


# ---------------------------------------------------------------------------
# 1. Victory progress
# ---------------------------------------------------------------------------

class TestVictoryProgress:
    def test_completed_agendas_score_higher(self):
        p_strong = _minimal_player(1, victory_progress={
            "a1": True, "a2": True, "a3": True,
        })
        p_weak = _minimal_player(2, victory_progress={"a1": True})
        state = _game([p_strong, p_weak])

        assert score_victory_progress(p_strong, state) > score_victory_progress(p_weak, state)

    def test_four_agendas_gives_bonus(self):
        p = _minimal_player(1, victory_progress={
            "a1": True, "a2": True, "a3": True, "a4": True,
        })
        state = _game([p])
        assert score_victory_progress(p, state) == min(4 * 75 + 50 + 75, 400.0)

    def test_false_entries_not_counted(self):
        p = _minimal_player(1, victory_progress={"a1": True, "a2": False})
        state = _game([p])
        assert score_victory_progress(p, state) == 75.0

    def test_no_progress(self):
        p = _minimal_player(1)
        state = _game([p])
        assert score_victory_progress(p, state) == 0.0

    def test_partial_progress_adds_points(self):
        p = _minimal_player(1, cities=(
            City(coord=HexCoord(0, 0), owner=1),
            City(coord=HexCoord(1, 0), owner=1),
            City(coord=HexCoord(2, 0), owner=1),
            City(coord=HexCoord(3, 0), owner=1),
        ))
        vc = VictoryCard(card_id="vc1", agenda_a="money_grubber", agenda_b="scholarly")
        state = _game([p], victory_cards=(vc,))
        score = score_victory_progress(p, state)
        assert score > 0.0
        assert score == pytest.approx((4 / 8) * 30.0, abs=0.1)

    def test_unknown_agenda_scores_zero_partial(self):
        p = _minimal_player(1)
        vc = VictoryCard(card_id="vc1", agenda_a="nonexistent_agenda", agenda_b="also_fake")
        state = _game([p], victory_cards=(vc,))
        assert score_victory_progress(p, state) == 0.0

    def test_completed_plus_partial(self):
        p = _minimal_player(1, victory_progress={"populous": True}, cities=(
            City(coord=HexCoord(i, 0), owner=1) for i in range(4)
        ))
        p = _minimal_player(1, victory_progress={"populous": True}, cities=tuple(
            City(coord=HexCoord(i, 0), owner=1) for i in range(4)
        ))
        vc = VictoryCard(card_id="vc1", agenda_a="populous", agenda_b="money_grubber")
        state = _game([p], victory_cards=(vc,))
        score = score_victory_progress(p, state)
        assert score >= 75.0


# ---------------------------------------------------------------------------
# 2. Territory
# ---------------------------------------------------------------------------

class TestTerritory:
    def test_more_spaces_scores_higher(self):
        tokens_10 = tuple(
            ControlToken(coord=HexCoord(i, 0), owner=1) for i in range(10)
        )
        tokens_3 = tuple(
            ControlToken(coord=HexCoord(i, 0), owner=2) for i in range(3)
        )
        tiles: dict[tuple[int, int], MapTile] = {}
        for i in range(10):
            tiles[(i, 0)] = MapTile(coord=HexCoord(i, 0), terrain="grassland")

        p1 = _minimal_player(1, control_tokens=tokens_10)
        p2 = _minimal_player(2, control_tokens=tokens_3)
        state = _game([p1, p2], map_tiles=tiles)

        assert score_territory(p1, state) > score_territory(p2, state)

    def test_resources_add_points(self):
        tokens = (ControlToken(coord=HexCoord(1, 0), owner=1),)
        p = _minimal_player(1, control_tokens=tokens)
        state = _game([p], map_tiles=_resource_map())
        score = score_territory(p, state)
        assert score >= 7.0

    def test_natural_wonder_adds_points(self):
        tokens = (ControlToken(coord=HexCoord(0, 1), owner=1),)
        p = _minimal_player(1, control_tokens=tokens)
        state = _game([p], map_tiles=_resource_map())
        score = score_territory(p, state)
        assert score >= 10.0

    def test_contiguity_bonus(self):
        connected = tuple(
            ControlToken(coord=HexCoord(i, 0), owner=1) for i in range(5)
        )
        fragmented = (
            ControlToken(coord=HexCoord(0, 0), owner=2),
            ControlToken(coord=HexCoord(5, 5), owner=2),
            ControlToken(coord=HexCoord(10, 10), owner=2),
            ControlToken(coord=HexCoord(15, 15), owner=2),
            ControlToken(coord=HexCoord(20, 20), owner=2),
        )
        tiles: dict[tuple[int, int], MapTile] = {}
        for i in range(5):
            tiles[(i, 0)] = MapTile(coord=HexCoord(i, 0), terrain="grassland")
        for q, r in [(0, 0), (5, 5), (10, 10), (15, 15), (20, 20)]:
            tiles[(q, r)] = MapTile(coord=HexCoord(q, r), terrain="grassland")

        p1 = _minimal_player(1, control_tokens=connected)
        p2 = _minimal_player(2, control_tokens=fragmented)
        state = _game([p1, p2], map_tiles=tiles)
        assert score_territory(p1, state) > score_territory(p2, state)

    def test_exploration_adjacency(self):
        tiles: dict[tuple[int, int], MapTile] = {
            (0, 0): MapTile(coord=HexCoord(0, 0), terrain="grassland"),
            (1, 0): MapTile(coord=HexCoord(1, 0), terrain="grassland", explored=False),
        }
        tokens = (ControlToken(coord=HexCoord(0, 0), owner=1),)
        p = _minimal_player(1, control_tokens=tokens)
        state = _game([p], map_tiles=tiles)
        score = score_territory(p, state)
        assert score > 2.0


# ---------------------------------------------------------------------------
# 3. Cities
# ---------------------------------------------------------------------------

class TestCities:
    def test_mature_with_wonder_beats_immature(self):
        p_strong = _minimal_player(1, cities=(
            City(coord=HexCoord(0, 0), owner=1, is_capital=True, is_mature=True, wonder="Pyramids"),
            City(coord=HexCoord(1, 0), owner=1, is_mature=True),
        ))
        p_weak = _minimal_player(2, cities=(
            City(coord=HexCoord(2, 0), owner=2),
            City(coord=HexCoord(3, 0), owner=2),
        ))
        state = _game([p_strong, p_weak])
        assert score_cities(p_strong, state) > score_cities(p_weak, state)

    def test_no_district_diversity_in_cities(self):
        tokens = (
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="campus"),
            ControlToken(coord=HexCoord(1, 0), owner=1, district_type="encampment"),
            ControlToken(coord=HexCoord(0, 1), owner=1, district_type="commercial_hub"),
        )
        p = _minimal_player(1, control_tokens=tokens)
        state = _game([p])
        assert score_cities(p, state) == 0.0


# ---------------------------------------------------------------------------
# 4. Tech
# ---------------------------------------------------------------------------

class TestTech:
    def test_higher_tech_scores_more(self):
        p_high = _minimal_player(1, tech_level=20)
        p_low = _minimal_player(2, tech_level=5)
        state = _game([p_high, p_low])
        assert score_tech(p_high, state) > score_tech(p_low, state)

    def test_level4_cards_bonus(self):
        cards = (
            FocusCard(card_type="science", slot=1, tech_level=4),
            FocusCard(card_type="culture", slot=2, tech_level=3),
        )
        p = _minimal_player(1, tech_level=0, focus_row=cards)
        state = _game([p])
        assert score_tech(p, state) == 15.0


# ---------------------------------------------------------------------------
# 5. Military
# ---------------------------------------------------------------------------

class TestMilitary:
    def test_deployed_armies_and_reinforced(self):
        p_strong = _minimal_player(1,
            armies=(
                Army(coord=HexCoord(0, 0), owner=1),
                Army(coord=HexCoord(1, 0), owner=1),
            ),
            control_tokens=(
                ControlToken(coord=HexCoord(2, 0), owner=1, reinforced=True),
            ),
        )
        p_weak = _minimal_player(2)
        state = _game([p_strong, p_weak])
        assert score_military(p_strong, state) > score_military(p_weak, state)
        assert score_military(p_strong, state) == 33.0

    def test_encampment_bonus(self):
        p = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="encampment"),
        ))
        state = _game([p])
        assert score_military(p, state) == 5.0

    def test_army_near_opponent_city(self):
        p1 = _minimal_player(1, armies=(
            Army(coord=HexCoord(1, 0), owner=1),
        ))
        p2 = _minimal_player(2, cities=(
            City(coord=HexCoord(2, 0), owner=2),
        ))
        state = _game([p1, p2])
        score = score_military(p1, state)
        assert score > 15.0

    def test_military_card_high_slot(self):
        p = _minimal_player(1, focus_row=(
            FocusCard(card_type="military", slot=5),
        ))
        state = _game([p])
        assert score_military(p, state) == 5.0


# ---------------------------------------------------------------------------
# 6. Economy
# ---------------------------------------------------------------------------

class TestEconomy:
    def test_trade_tokens_and_caravans(self):
        p_strong = _minimal_player(1,
            trade_tokens_total=10,
            caravans=(
                Caravan(coord=HexCoord(0, 0), owner=1),
                Caravan(coord=HexCoord(1, 0), owner=1),
            ),
            cities=(City(coord=HexCoord(2, 0), owner=1, is_mature=True),),
        )
        p_weak = _minimal_player(2, trade_tokens_total=1)
        state = _game([p_strong, p_weak])
        assert score_economy(p_strong, state) > score_economy(p_weak, state)
        assert score_economy(p_strong, state) >= 55.0

    def test_commercial_hub_bonus(self):
        p = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="commercial_hub"),
        ))
        state = _game([p])
        assert score_economy(p, state) == 5.0

    def test_caravan_near_city_state(self):
        tiles: dict[tuple[int, int], MapTile] = {
            (0, 0): MapTile(coord=HexCoord(0, 0), terrain="grassland"),
            (1, 0): MapTile(coord=HexCoord(1, 0), terrain="grassland", has_city_state="toronto"),
        }
        p = _minimal_player(1, caravans=(
            Caravan(coord=HexCoord(0, 0), owner=1),
        ))
        state = _game([p], map_tiles=tiles)
        score = score_economy(p, state)
        assert score > 10.0


# ---------------------------------------------------------------------------
# 7. Wonders
# ---------------------------------------------------------------------------

class TestWonders:
    def test_era_weighted_scoring(self):
        p_ancient = _minimal_player(1, wonders_built=("stonehenge",))
        p_modern = _minimal_player(2, wonders_built=("broadway",))
        state = _game([p_ancient, p_modern])
        assert score_wonders(p_modern, state) > score_wonders(p_ancient, state)
        assert score_wonders(p_ancient, state) == 10.0
        assert score_wonders(p_modern, state) == 25.0

    def test_unknown_wonder_default_score(self):
        p = _minimal_player(1, wonders_built=("unknown_wonder",))
        state = _game([p])
        assert score_wonders(p, state) == 15.0

    def test_count_bonuses(self):
        p = _minimal_player(1, wonders_built=(
            "stonehenge", "pyramids", "colosseum",
        ))
        state = _game([p])
        assert score_wonders(p, state) == 3 * 10 + 10


# ---------------------------------------------------------------------------
# 8. Focus row
# ---------------------------------------------------------------------------

class TestFocusRow:
    def test_high_slots_score_more(self):
        p_high = _minimal_player(1, focus_row=(
            FocusCard(card_type="culture", slot=5),
            FocusCard(card_type="science", slot=4),
        ))
        p_low = _minimal_player(2, focus_row=(
            FocusCard(card_type="culture", slot=1),
            FocusCard(card_type="science", slot=2),
        ))
        assert score_focus_row(p_high) > score_focus_row(p_low)

    def test_government_and_trade_tokens(self):
        p = _minimal_player(1, focus_row=(
            FocusCard(card_type="culture", slot=3, has_government=True, trade_tokens=2),
        ))
        # slot>=3: 3 + government: 3 + arrows(0)*2: 0 + trade_tokens: 2 = 8
        assert score_focus_row(p) == 8.0

    def test_government_arrows_boost(self):
        p = _minimal_player(1, focus_row=(
            FocusCard(card_type="culture", slot=2, has_government=True, government_arrows=2),
        ))
        # effective_slot = min(2+2, 5) = 4 -> 6pts. government: 3 + 2*2=4 -> 7pts. total=13
        assert score_focus_row(p) == 13.0

    def test_effective_slot_capped_at_5(self):
        p = _minimal_player(1, focus_row=(
            FocusCard(card_type="culture", slot=4, has_government=True, government_arrows=3),
        ))
        # effective_slot = min(4+3, 5) = 5 -> 10pts. government: 3 + 3*2=6 -> 9pts. total=19
        assert score_focus_row(p) == 19.0


# ---------------------------------------------------------------------------
# 9. Diplomacy
# ---------------------------------------------------------------------------

class TestDiplomacy:
    def test_diplomacy_scoring(self):
        p = _minimal_player(1, diplomacy_cards=("a", "b", "c"))
        state = _game([p])
        assert score_diplomacy(p, state) == 3 * 8 + 10


# ---------------------------------------------------------------------------
# 10. Districts [NEW]
# ---------------------------------------------------------------------------

class TestDistricts:
    def test_campus_near_mountain(self):
        tiles: dict[tuple[int, int], MapTile] = {
            (0, 0): MapTile(coord=HexCoord(0, 0), terrain="grassland"),
            (1, 0): MapTile(coord=HexCoord(1, 0), terrain="mountain"),
            (0, 1): MapTile(coord=HexCoord(0, 1), terrain="mountain"),
        }
        p = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="campus"),
        ))
        state = _game([p], map_tiles=tiles)
        score = score_districts(p, state)
        assert score == 4.0 + 4.0 + 4.0  # diversity(1*4) + 2 mountains(2*4)

    def test_campus_near_natural_wonder(self):
        tiles: dict[tuple[int, int], MapTile] = {
            (0, 0): MapTile(coord=HexCoord(0, 0), terrain="grassland"),
            (1, 0): MapTile(coord=HexCoord(1, 0), terrain="grassland", has_natural_wonder="reef"),
        }
        p = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="campus"),
        ))
        state = _game([p], map_tiles=tiles)
        assert score_districts(p, state) == 4.0 + 6.0  # diversity + wonder

    def test_commercial_hub_near_desert(self):
        tiles: dict[tuple[int, int], MapTile] = {
            (0, 0): MapTile(coord=HexCoord(0, 0), terrain="grassland"),
            (1, 0): MapTile(coord=HexCoord(1, 0), terrain="desert"),
            (0, 1): MapTile(coord=HexCoord(0, 1), terrain="desert"),
        }
        p = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="commercial_hub"),
        ))
        state = _game([p], map_tiles=tiles)
        score = score_districts(p, state)
        assert score == 4.0 + 3.0 + 3.0  # diversity + 2 deserts

    def test_encampment_near_rival(self):
        p1 = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="encampment"),
        ))
        p2 = _minimal_player(2, cities=(
            City(coord=HexCoord(1, 0), owner=2),
        ))
        state = _game([p1, p2])
        score = score_districts(p1, state)
        assert score > 4.0  # diversity + proximity bonus

    def test_industrial_zone_near_forest(self):
        tiles: dict[tuple[int, int], MapTile] = {
            (0, 0): MapTile(coord=HexCoord(0, 0), terrain="grassland"),
            (1, 0): MapTile(coord=HexCoord(1, 0), terrain="forest"),
        }
        p = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="industrial_zone"),
        ))
        state = _game([p], map_tiles=tiles)
        assert score_districts(p, state) == 4.0 + 4.0

    def test_theater_square_near_wonder_city(self):
        p = _minimal_player(1,
            control_tokens=(
                ControlToken(coord=HexCoord(0, 0), owner=1, district_type="theater_square"),
            ),
            cities=(
                City(coord=HexCoord(1, 0), owner=1, wonder="pyramids"),
            ),
        )
        state = _game([p])
        assert score_districts(p, state) == 4.0 + 5.0

    def test_diversity_bonus(self):
        p = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1, district_type="campus"),
            ControlToken(coord=HexCoord(1, 0), owner=1, district_type="encampment"),
            ControlToken(coord=HexCoord(0, 1), owner=1, district_type="commercial_hub"),
        ))
        state = _game([p])
        score = score_districts(p, state)
        assert score >= 12.0  # 3 types * 4

    def test_district_cap(self):
        tiles: dict[tuple[int, int], MapTile] = {}
        tokens = []
        for i in range(20):
            tiles[(i, 0)] = MapTile(coord=HexCoord(i, 0), terrain="mountain",
                                     has_natural_wonder="w")
            tokens.append(ControlToken(coord=HexCoord(i, 0), owner=1, district_type="campus"))
        p = _minimal_player(1, control_tokens=tuple(tokens))
        state = _game([p], map_tiles=tiles)
        assert score_districts(p, state) <= 80.0


# ---------------------------------------------------------------------------
# 11. Resources [NEW]
# ---------------------------------------------------------------------------

class TestResources:
    def test_resource_count(self):
        p = _minimal_player(1, resources=("marble", "oil"))
        state = _game([p])
        score = score_resources(p, state)
        assert score == 2 * 5 + 2 * 3  # 2 resources * 5 + 2 unique * 3

    def test_diversity_bonus(self):
        p = _minimal_player(1, resources=("marble", "oil", "mercury", "diamond"))
        state = _game([p])
        score = score_resources(p, state)
        assert score == 4 * 5 + 4 * 3 + 8  # 4 resources + 4 unique + full diversity

    def test_natural_wonder_tokens(self):
        p = _minimal_player(1, natural_wonders=("reef", "mesa"))
        state = _game([p])
        score = score_resources(p, state)
        assert score == 2 * 8  # 2 NW * 8

    def test_resource_cap(self):
        p = _minimal_player(1,
            resources=tuple(f"r{i}" for i in range(20)),
            natural_wonders=tuple(f"nw{i}" for i in range(10)),
        )
        state = _game([p])
        assert score_resources(p, state) <= 50.0


# ---------------------------------------------------------------------------
# 12. Forts [NEW]
# ---------------------------------------------------------------------------

class TestForts:
    def test_fort_city_scoring(self):
        p = _minimal_player(1, cities=(
            City(coord=HexCoord(0, 0), owner=1, on_fort=True),
        ))
        state = _game([p])
        assert score_forts(p, state) == 12.0

    def test_fort_victory_card_bonus(self):
        p = _minimal_player(1, cities=(
            City(coord=HexCoord(0, 0), owner=1, on_fort=True),
        ))
        vc = VictoryCard(card_id="fort1", is_fort_card=True)
        state = _game([p], victory_cards=(vc,))
        assert score_forts(p, state) == 12.0 + 8.0

    def test_unclaimed_fort_proximity(self):
        tiles: dict[tuple[int, int], MapTile] = {
            (0, 0): MapTile(coord=HexCoord(0, 0), terrain="grassland"),
            (2, 0): MapTile(coord=HexCoord(2, 0), terrain="forest", has_fort=True),
        }
        p = _minimal_player(1, cities=(
            City(coord=HexCoord(0, 0), owner=1),
        ))
        state = _game([p], map_tiles=tiles)
        score = score_forts(p, state)
        assert score > 0.0

    def test_fort_cap(self):
        cities = tuple(
            City(coord=HexCoord(i, 0), owner=1, on_fort=True) for i in range(10)
        )
        vc = VictoryCard(card_id="fort1", is_fort_card=True)
        p = _minimal_player(1, cities=cities)
        state = _game([p], victory_cards=(vc,))
        assert score_forts(p, state) <= 40.0


# ---------------------------------------------------------------------------
# 13. Position [NEW]
# ---------------------------------------------------------------------------

class TestPosition:
    def test_edge_city_bonus(self):
        tiles: dict[tuple[int, int], MapTile] = {
            (0, 0): MapTile(coord=HexCoord(0, 0), terrain="grassland"),
            (1, 0): MapTile(coord=HexCoord(1, 0), terrain="grassland"),
        }
        p = _minimal_player(1, cities=(
            City(coord=HexCoord(0, 0), owner=1),
        ))
        state = _game([p], map_tiles=tiles)
        score = score_position(p, state)
        assert score > 0.0

    def test_contiguity_bonus(self):
        connected_tokens = tuple(
            ControlToken(coord=HexCoord(i, 0), owner=1) for i in range(5)
        )
        tiles: dict[tuple[int, int], MapTile] = {}
        for i in range(5):
            tiles[(i, 0)] = MapTile(coord=HexCoord(i, 0), terrain="grassland")

        p = _minimal_player(1, control_tokens=connected_tokens)
        state = _game([p], map_tiles=tiles)
        score = score_position(p, state)
        assert score >= 15.0  # fully connected = ratio 1.0 * 15

    def test_frontier_pressure(self):
        p1 = _minimal_player(1, control_tokens=(
            ControlToken(coord=HexCoord(0, 0), owner=1),
        ))
        p2 = _minimal_player(2, control_tokens=(
            ControlToken(coord=HexCoord(1, 0), owner=2),
        ))
        state = _game([p1, p2])
        score = score_position(p1, state)
        assert score >= 1.5

    def test_position_cap(self):
        cities = tuple(
            City(coord=HexCoord(i * 10, j * 10), owner=1) for i in range(5) for j in range(5)
        )
        tokens = tuple(
            ControlToken(coord=HexCoord(i, 0), owner=1) for i in range(50)
        )
        tiles: dict[tuple[int, int], MapTile] = {}
        for c in cities:
            tiles[(c.coord.q, c.coord.r)] = MapTile(
                coord=c.coord, terrain="grassland",
            )
        for ct in tokens:
            tiles[(ct.coord.q, ct.coord.r)] = MapTile(
                coord=ct.coord, terrain="grassland",
            )
        p = _minimal_player(1, cities=cities, control_tokens=tokens)
        state = _game([p], map_tiles=tiles)
        assert score_position(p, state) <= 60.0


# ---------------------------------------------------------------------------
# Overall evaluate_position
# ---------------------------------------------------------------------------

class TestEvaluatePosition:
    def test_stronger_player_scores_higher(self):
        p1 = _minimal_player(1,
            victory_progress={"a1": True, "a2": True},
            tech_level=15,
            cities=(
                City(coord=HexCoord(0, 0), owner=1, is_capital=True, is_mature=True),
            ),
            control_tokens=tuple(
                ControlToken(coord=HexCoord(i, 0), owner=1) for i in range(1, 6)
            ),
            armies=(Army(coord=HexCoord(0, 1), owner=1),),
            trade_tokens_total=8,
            resources=("marble", "oil"),
        )
        p2 = _minimal_player(2, tech_level=3)
        state = _game([p1, p2])
        scores = evaluate_position(state)
        assert scores[1] > scores[2]

    def test_returns_score_for_each_player(self):
        state = _game([_minimal_player(1), _minimal_player(2), _minimal_player(3)])
        scores = evaluate_position(state)
        assert set(scores.keys()) == {1, 2, 3}


# ---------------------------------------------------------------------------
# Caps
# ---------------------------------------------------------------------------

class TestCaps:
    def test_victory_cap(self):
        p = _minimal_player(1, victory_progress={
            f"a{i}": True for i in range(10)
        })
        state = _game([p])
        assert score_victory_progress(p, state) <= 400.0

    def test_territory_cap(self):
        tokens = tuple(
            ControlToken(coord=HexCoord(i, j), owner=1)
            for i in range(20) for j in range(5)
        )
        tiles: dict[tuple[int, int], MapTile] = {}
        for i in range(20):
            for j in range(5):
                tiles[(i, j)] = MapTile(
                    coord=HexCoord(i, j), terrain="grassland",
                    has_resource="marble", has_natural_wonder="wonder",
                )
        p = _minimal_player(1, control_tokens=tokens)
        state = _game([p], map_tiles=tiles)
        assert score_territory(p, state) <= 140.0

    def test_cities_cap(self):
        cities = tuple(
            City(coord=HexCoord(i, 0), owner=1, is_capital=(i == 0),
                 is_mature=True, wonder="W", on_fort=True)
            for i in range(15)
        )
        p = _minimal_player(1, cities=cities)
        state = _game([p])
        assert score_cities(p, state) <= 150.0

    def test_tech_cap(self):
        cards = tuple(
            FocusCard(card_type="science", slot=1, tech_level=4)
            for _ in range(10)
        )
        p = _minimal_player(1, tech_level=50, focus_row=cards)
        state = _game([p])
        assert score_tech(p, state) <= 100.0

    def test_military_cap(self):
        armies = tuple(Army(coord=HexCoord(i, 0), owner=1) for i in range(10))
        tokens = tuple(
            ControlToken(coord=HexCoord(i, 1), owner=1, reinforced=True,
                         district_type="encampment")
            for i in range(10)
        )
        p = _minimal_player(1, armies=armies, control_tokens=tokens,
                            cities=(City(coord=HexCoord(0, 0), owner=1, on_fort=True),))
        state = _game([p])
        assert score_military(p, state) <= 100.0

    def test_economy_cap(self):
        caravans = tuple(Caravan(coord=HexCoord(i, 0), owner=1) for i in range(10))
        p = _minimal_player(1, trade_tokens_total=50, caravans=caravans,
                            cities=(City(coord=HexCoord(0, 0), owner=1, is_mature=True),))
        state = _game([p])
        assert score_economy(p, state) <= 90.0

    def test_wonders_cap(self):
        p = _minimal_player(1, wonders_built=tuple(f"W{i}" for i in range(10)))
        state = _game([p])
        assert score_wonders(p, state) <= 90.0

    def test_focus_row_cap(self):
        cards = tuple(
            FocusCard(card_type="culture", slot=5, has_government=True,
                      government_arrows=3, trade_tokens=3)
            for _ in range(5)
        )
        p = _minimal_player(1, focus_row=cards)
        assert score_focus_row(p) <= 70.0

    def test_diplomacy_cap(self):
        p = _minimal_player(1, diplomacy_cards=tuple(f"d{i}" for i in range(10)))
        state = _game([p])
        assert score_diplomacy(p, state) <= 50.0


# ---------------------------------------------------------------------------
# Empty / minimal state
# ---------------------------------------------------------------------------

class TestEmptyState:
    def test_no_crash_on_empty(self):
        p = _minimal_player(1)
        state = _game([p])
        scores = evaluate_position(state)
        assert scores[1] == 0.0

    def test_no_crash_no_players(self):
        state = CivGameState(map_tiles={}, players=(), current_player=0)
        scores = evaluate_position(state)
        assert scores == {}
