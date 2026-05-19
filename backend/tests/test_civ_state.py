"""Tests for the Civilization: A New Dawn game state model and parser."""

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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _full_game_data() -> dict:
    """Return a realistic game_data dict for parsing tests."""
    return {
        "map": [
            {"q": 0, "r": 0, "terrain": "grassland", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": 1, "r": 0, "terrain": "hills", "resource": "marble", "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": 0, "r": 1, "terrain": "water", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": 1, "r": -1, "terrain": "forest", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": True, "explored": True},
            {"q": -1, "r": 0, "terrain": "desert", "resource": "oil", "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": -1, "r": 1, "terrain": "mountain", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": False},
            {"q": 0, "r": -1, "terrain": "grassland", "resource": None, "natural_wonder": None,
             "barbarian": True, "city_state": None, "fort": False, "explored": True},
            {"q": 5, "r": -2, "terrain": "grassland", "resource": None, "natural_wonder": "great_barrier_reef",
             "barbarian": False, "city_state": "toronto", "fort": False, "explored": True},
        ],
        "players": [
            {
                "id": 1,
                "leader": "Rome",
                "government": "democracy",
                "focus_row": [
                    {"type": "culture", "slot": 1, "tech_level": 2, "trade_tokens": 1, "government": False},
                    {"type": "science", "slot": 2, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "economy", "slot": 3, "tech_level": 3, "trade_tokens": 2, "government": True, "government_arrows": 2},
                    {"type": "industry", "slot": 4, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "military", "slot": 5, "tech_level": 2, "trade_tokens": 0, "government": False},
                ],
                "tech_level": 12,
                "cities": [
                    {"q": 0, "r": 0, "is_capital": True, "is_mature": True, "wonder": None, "on_fort": False},
                ],
                "control_tokens": [
                    {"q": 1, "r": 0, "reinforced": False, "district": None},
                    {"q": 1, "r": -1, "reinforced": True, "district": "encampment"},
                ],
                "armies": [{"q": 2, "r": -1}, None],
                "caravans": [None, {"q": 3, "r": 0}],
                "resources": ["marble", "diamond"],
                "natural_wonders": ["great_barrier_reef"],
                "trade_tokens_total": 8,
                "diplomacy_cards": ["rome_card"],
                "wonders_built": ["colosseum"],
                "victory_progress": {"populous": True, "explorer": False},
            },
            {
                "id": 2,
                "leader": "Egypt",
                "government": None,
                "focus_row": [
                    {"type": "culture", "slot": 1, "tech_level": 1, "trade_tokens": 0, "government": False},
                ],
                "tech_level": 5,
                "cities": [
                    {"q": -1, "r": 0, "is_capital": True, "is_mature": False, "wonder": "pyramids", "on_fort": False},
                ],
                "control_tokens": [],
                "armies": [],
                "caravans": [],
                "resources": ["oil"],
                "natural_wonders": [],
                "trade_tokens_total": 2,
                "diplomacy_cards": [],
                "wonders_built": ["pyramids"],
                "victory_progress": {},
            },
        ],
        "victory_cards": [
            {"id": "vc1", "agenda_a": "populous", "agenda_b": "explorer", "is_fort_card": False},
            {"id": "vc2", "agenda_a": "militaristic", "agenda_b": "trader", "is_fort_card": True},
        ],
        "event_dial": 3,
        "turn_number": 15,
        "current_player": 1,
        "move_number": 42,
        "barbarians": [{"q": 5, "r": -2}, {"q": 3, "r": 1}],
    }


# ---------------------------------------------------------------------------
# 1. Full parse
# ---------------------------------------------------------------------------

class TestFullParse:
    def test_parse_complete_game_data(self):
        state = CivGameState.from_game_data(_full_game_data())

        assert len(state.map_tiles) == 8
        assert len(state.players) == 2
        assert state.current_player == 1
        assert state.move_number == 42
        assert state.event_dial_position == 3
        assert state.turn_number == 15
        assert len(state.victory_cards) == 2
        assert len(state.barbarian_positions) == 2

    def test_player_fields(self):
        state = CivGameState.from_game_data(_full_game_data())
        p1 = state.get_player(1)
        assert p1 is not None
        assert p1.leader == "Rome"
        assert p1.government == "democracy"
        assert p1.tech_level == 12
        assert len(p1.focus_row) == 5
        assert len(p1.cities) == 1
        assert len(p1.control_tokens) == 2
        assert len(p1.armies) == 2
        assert len(p1.caravans) == 2
        assert p1.resources == ("marble", "diamond")
        assert p1.natural_wonders == ("great_barrier_reef",)
        assert p1.trade_tokens_total == 8
        assert p1.diplomacy_cards == ("rome_card",)
        assert p1.wonders_built == ("colosseum",)
        assert p1.victory_progress == {"populous": True, "explorer": False}

    def test_map_tile_fields(self):
        state = CivGameState.from_game_data(_full_game_data())
        tile = state.get_tile(1, 0)
        assert tile is not None
        assert tile.terrain == "hills"
        assert tile.has_resource == "marble"
        assert tile.has_natural_wonder is None
        assert tile.has_barbarian is False
        assert tile.has_fort is False
        assert tile.explored is True

    def test_tile_with_barbarian_and_city_state(self):
        state = CivGameState.from_game_data(_full_game_data())
        tile = state.get_tile(5, -2)
        assert tile is not None
        assert tile.has_natural_wonder == "great_barrier_reef"
        assert tile.has_city_state == "toronto"

    def test_unexplored_tile(self):
        state = CivGameState.from_game_data(_full_game_data())
        tile = state.get_tile(-1, 1)
        assert tile is not None
        assert tile.explored is False
        assert tile.terrain == "mountain"

    def test_victory_cards(self):
        state = CivGameState.from_game_data(_full_game_data())
        vc1, vc2 = state.victory_cards
        assert vc1.card_id == "vc1"
        assert vc1.agenda_a == "populous"
        assert vc1.agenda_b == "explorer"
        assert vc1.is_fort_card is False
        assert vc2.is_fort_card is True

    def test_barbarian_positions(self):
        state = CivGameState.from_game_data(_full_game_data())
        coords = [(b.q, b.r) for b in state.barbarian_positions]
        assert (5, -2) in coords
        assert (3, 1) in coords


# ---------------------------------------------------------------------------
# 2. Missing fields
# ---------------------------------------------------------------------------

class TestMissingFields:
    def test_missing_keys_uses_defaults(self):
        data = {
            "map": [{"q": 0, "r": 0}],  # minimal tile
            "players": [{"id": 1}],      # minimal player
        }
        state = CivGameState.from_game_data(data)
        tile = state.get_tile(0, 0)
        assert tile is not None
        assert tile.terrain == "grassland"
        assert tile.has_resource is None
        assert tile.explored is True

        p = state.get_player(1)
        assert p is not None
        assert p.leader == ""
        assert p.government is None
        assert p.focus_row == ()
        assert p.tech_level == 0
        assert p.cities == ()
        assert p.resources == ()


# ---------------------------------------------------------------------------
# 3. Empty dict
# ---------------------------------------------------------------------------

class TestEmptyData:
    def test_empty_dict_returns_valid_state(self):
        state = CivGameState.from_game_data({})
        assert state.map_tiles == {}
        assert state.players == ()
        assert state.current_player == 1
        assert state.move_number == 0
        assert state.victory_cards == ()
        assert state.event_dial_position == 0
        assert state.turn_number == 0
        assert state.barbarian_positions == ()


# ---------------------------------------------------------------------------
# 4. get_player
# ---------------------------------------------------------------------------

class TestGetPlayer:
    def test_returns_correct_player(self):
        state = CivGameState.from_game_data(_full_game_data())
        p2 = state.get_player(2)
        assert p2 is not None
        assert p2.leader == "Egypt"

    def test_returns_none_for_missing(self):
        state = CivGameState.from_game_data(_full_game_data())
        assert state.get_player(99) is None

    def test_returns_none_on_empty_state(self):
        state = CivGameState.from_game_data({})
        assert state.get_player(1) is None


# ---------------------------------------------------------------------------
# 5. get_tile
# ---------------------------------------------------------------------------

class TestGetTile:
    def test_returns_correct_tile(self):
        state = CivGameState.from_game_data(_full_game_data())
        tile = state.get_tile(0, 0)
        assert tile is not None
        assert tile.terrain == "grassland"

    def test_returns_none_for_missing(self):
        state = CivGameState.from_game_data(_full_game_data())
        assert state.get_tile(99, 99) is None


# ---------------------------------------------------------------------------
# 6. friendly_spaces
# ---------------------------------------------------------------------------

class TestFriendlySpaces:
    def test_includes_cities_and_tokens(self):
        state = CivGameState.from_game_data(_full_game_data())
        friendly = state.friendly_spaces(1)
        # Player 1 has city at (0,0), tokens at (1,0) and (1,-1)
        assert (0, 0) in friendly
        assert (1, 0) in friendly
        assert (1, -1) in friendly
        assert len(friendly) == 3

    def test_empty_for_unknown_player(self):
        state = CivGameState.from_game_data(_full_game_data())
        assert state.friendly_spaces(99) == set()

    def test_player_with_no_pieces(self):
        """Player 2 has a city but no control tokens."""
        state = CivGameState.from_game_data(_full_game_data())
        friendly = state.friendly_spaces(2)
        assert (-1, 0) in friendly
        assert len(friendly) == 1


# ---------------------------------------------------------------------------
# 7. is_city_mature
# ---------------------------------------------------------------------------

class TestIsCityMature:
    def _build_surrounded_state(self, neighbor_terrains: dict[tuple[int, int], str],
                                 friendly_coords: set[tuple[int, int]]) -> CivGameState:
        """Build a minimal state with a city at (0,0) and specified neighbors."""
        tiles_raw = [{"q": 0, "r": 0, "terrain": "grassland"}]
        for (q, r), terrain in neighbor_terrains.items():
            tiles_raw.append({"q": q, "r": r, "terrain": terrain})

        tokens_raw = [{"q": q, "r": r} for q, r in friendly_coords]

        data = {
            "map": tiles_raw,
            "players": [{
                "id": 1,
                "cities": [{"q": 0, "r": 0, "is_capital": True}],
                "control_tokens": tokens_raw,
            }],
        }
        return CivGameState.from_game_data(data)

    def test_mature_all_friendly(self):
        """All 6 neighbors have control tokens -> mature."""
        from app.engine.civilization.hex_map import hex_neighbors
        neighbors = hex_neighbors(0, 0)
        neighbor_terrains = {(q, r): "grassland" for q, r in neighbors}
        friendly = {(q, r) for q, r in neighbors}
        state = self._build_surrounded_state(neighbor_terrains, friendly)
        city = state.get_player(1).cities[0]
        assert state.is_city_mature(city) is True

    def test_mature_with_water_neighbors(self):
        """Some neighbors are water (no token needed), rest are friendly -> mature."""
        from app.engine.civilization.hex_map import hex_neighbors
        neighbors = hex_neighbors(0, 0)
        neighbor_terrains = {}
        friendly = set()
        for i, (q, r) in enumerate(neighbors):
            if i < 3:
                neighbor_terrains[(q, r)] = "water"
            else:
                neighbor_terrains[(q, r)] = "grassland"
                friendly.add((q, r))

        state = self._build_surrounded_state(neighbor_terrains, friendly)
        city = state.get_player(1).cities[0]
        assert state.is_city_mature(city) is True

    def test_not_mature_missing_friendly(self):
        """One neighbor is land with no token -> not mature."""
        from app.engine.civilization.hex_map import hex_neighbors
        neighbors = hex_neighbors(0, 0)
        neighbor_terrains = {(q, r): "grassland" for q, r in neighbors}
        # Leave one neighbor without a token
        friendly = {(q, r) for q, r in neighbors[:-1]}
        state = self._build_surrounded_state(neighbor_terrains, friendly)
        city = state.get_player(1).cities[0]
        assert state.is_city_mature(city) is False

    def test_not_mature_off_map_neighbor(self):
        """If a neighbor hex is not on the map at all, city is not mature."""
        # Only add some neighbors to the map; others are off-map
        neighbor_terrains = {(1, 0): "grassland"}
        friendly = {(1, 0)}
        state = self._build_surrounded_state(neighbor_terrains, friendly)
        city = state.get_player(1).cities[0]
        assert state.is_city_mature(city) is False


# ---------------------------------------------------------------------------
# 8. Individual dataclass parsing
# ---------------------------------------------------------------------------

class TestIndividualParsing:
    def test_focus_card_parsing(self):
        state = CivGameState.from_game_data(_full_game_data())
        p1 = state.get_player(1)
        fc = p1.focus_row[2]  # economy card
        assert fc.card_type == "economy"
        assert fc.slot == 3
        assert fc.tech_level == 3
        assert fc.trade_tokens == 2
        assert fc.has_government is True

    def test_city_parsing(self):
        state = CivGameState.from_game_data(_full_game_data())
        p1 = state.get_player(1)
        city = p1.cities[0]
        assert city.coord == HexCoord(0, 0)
        assert city.owner == 1
        assert city.is_capital is True
        assert city.is_mature is True
        assert city.wonder is None
        assert city.on_fort is False

    def test_city_with_wonder(self):
        state = CivGameState.from_game_data(_full_game_data())
        p2 = state.get_player(2)
        city = p2.cities[0]
        assert city.wonder == "pyramids"

    def test_control_token_parsing(self):
        state = CivGameState.from_game_data(_full_game_data())
        p1 = state.get_player(1)

        plain = p1.control_tokens[0]
        assert plain.coord == HexCoord(1, 0)
        assert plain.reinforced is False
        assert plain.district_type is None

        district = p1.control_tokens[1]
        assert district.coord == HexCoord(1, -1)
        assert district.reinforced is True
        assert district.district_type == "encampment"

    def test_army_on_map_and_on_card(self):
        state = CivGameState.from_game_data(_full_game_data())
        p1 = state.get_player(1)
        assert p1.armies[0].coord == HexCoord(2, -1)
        assert p1.armies[1].coord is None  # on card

    def test_caravan_on_map_and_on_card(self):
        state = CivGameState.from_game_data(_full_game_data())
        p1 = state.get_player(1)
        assert p1.caravans[0].coord is None  # on card
        assert p1.caravans[1].coord == HexCoord(3, 0)

    def test_tile_with_fort(self):
        state = CivGameState.from_game_data(_full_game_data())
        tile = state.get_tile(1, -1)
        assert tile.has_fort is True
        assert tile.terrain == "forest"

    def test_government_arrows_parsing(self):
        state = CivGameState.from_game_data(_full_game_data())
        p1 = state.get_player(1)
        economy_card = p1.focus_row[2]
        assert economy_card.government_arrows == 2

    def test_government_arrows_default(self):
        state = CivGameState.from_game_data(_full_game_data())
        p1 = state.get_player(1)
        culture_card = p1.focus_row[0]
        assert culture_card.government_arrows == 0


# ---------------------------------------------------------------------------
# 9. New v2 helpers
# ---------------------------------------------------------------------------

class TestNewHelpers:
    def test_all_opponent_cities(self):
        state = CivGameState.from_game_data(_full_game_data())
        opp = state.all_opponent_cities(1)
        assert len(opp) == 1
        assert opp[0].owner == 2

    def test_all_opponent_cities_empty(self):
        state = CivGameState.from_game_data(_full_game_data())
        opp = state.all_opponent_cities(99)
        assert len(opp) == 2  # both players' cities

    def test_tiles_adjacent_to(self):
        state = CivGameState.from_game_data(_full_game_data())
        adj = state.tiles_adjacent_to(0, 0)
        assert len(adj) > 0
        coords = {(t.coord.q, t.coord.r) for t in adj}
        assert (1, 0) in coords
        assert (0, 1) in coords

    def test_tiles_adjacent_to_off_map(self):
        state = CivGameState.from_game_data(_full_game_data())
        adj = state.tiles_adjacent_to(99, 99)
        assert len(adj) == 0

    def test_territory_components_connected(self):
        data = {
            "map": [{"q": i, "r": 0} for i in range(5)],
            "players": [{
                "id": 1,
                "control_tokens": [{"q": i, "r": 0} for i in range(5)],
            }],
        }
        state = CivGameState.from_game_data(data)
        components = state.territory_components(1)
        assert len(components) == 1
        assert len(components[0]) == 5

    def test_territory_components_fragmented(self):
        data = {
            "map": [{"q": 0, "r": 0}, {"q": 10, "r": 10}],
            "players": [{
                "id": 1,
                "control_tokens": [{"q": 0, "r": 0}, {"q": 10, "r": 10}],
            }],
        }
        state = CivGameState.from_game_data(data)
        components = state.territory_components(1)
        assert len(components) == 2
