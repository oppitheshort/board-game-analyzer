"""Integration tests for Civilization: A New Dawn engine and backwards compatibility."""

import pytest

from app.engine.civilization.state import CivGameState, HexCoord
from app.engine.civilization.hex_map import hex_neighbors, hex_distance
from app.schemas.board import BoardStateMessage
from app.schemas.analysis import MomentumPoint, PlayerStrength
from app.ws.analysis_handler import compute_player_strength, compute_momentum


# ---------------------------------------------------------------------------
# Fixture: realistic 3-player game state
# ---------------------------------------------------------------------------

def make_sample_game_data() -> dict:
    """Build a realistic 3-player Civ game state."""
    return {
        "map": [
            {"q": 0, "r": 0, "terrain": "grassland", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": 1, "r": 0, "terrain": "hills", "resource": "marble", "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": 0, "r": 1, "terrain": "forest", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": -1, "r": 1, "terrain": "desert", "resource": "oil", "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": 1, "r": -1, "terrain": "water", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": -1, "r": 0, "terrain": "mountain", "resource": None, "natural_wonder": "great_barrier_reef",
             "barbarian": False, "city_state": None, "fort": False, "explored": True},
            {"q": 0, "r": -1, "terrain": "grassland", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": "buenos_aires", "fort": False, "explored": True},
            {"q": 2, "r": -1, "terrain": "hills", "resource": None, "natural_wonder": None,
             "barbarian": True, "city_state": None, "fort": False, "explored": True},
            {"q": 3, "r": 0, "terrain": "grassland", "resource": None, "natural_wonder": None,
             "barbarian": False, "city_state": None, "fort": True, "explored": True},
        ],
        "players": [
            {
                "id": 1, "leader": "Rome", "government": "democracy",
                "focus_row": [
                    {"type": "culture", "slot": 3, "tech_level": 2, "trade_tokens": 1, "government": False},
                    {"type": "science", "slot": 1, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "economy", "slot": 5, "tech_level": 2, "trade_tokens": 2, "government": True, "government_arrows": 2},
                    {"type": "industry", "slot": 2, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "military", "slot": 4, "tech_level": 3, "trade_tokens": 1, "government": False},
                    {"type": "growth", "slot": 1, "tech_level": 1, "trade_tokens": 0, "government": False},
                ],
                "tech_level": 14,
                "cities": [
                    {"q": 0, "r": 0, "is_capital": True, "is_mature": True, "wonder": "colosseum", "on_fort": False},
                    {"q": -1, "r": 1, "is_capital": False, "is_mature": False, "wonder": None, "on_fort": False},
                ],
                "control_tokens": [
                    {"q": 1, "r": 0, "reinforced": True, "district": None},
                    {"q": 0, "r": 1, "reinforced": False, "district": "campus"},
                ],
                "armies": [{"q": 2, "r": 0}, None],
                "caravans": [None, {"q": 3, "r": -1}],
                "resources": ["marble", "oil"],
                "natural_wonders": [],
                "trade_tokens_total": 6,
                "diplomacy_cards": ["egypt_card"],
                "wonders_built": ["colosseum"],
                "victory_progress": {"populous": True, "explorer": False},
            },
            {
                "id": 2, "leader": "Egypt", "government": None,
                "focus_row": [
                    {"type": "culture", "slot": 1, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "science", "slot": 4, "tech_level": 2, "trade_tokens": 1, "government": False},
                    {"type": "economy", "slot": 2, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "industry", "slot": 3, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "military", "slot": 1, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "growth", "slot": 5, "tech_level": 1, "trade_tokens": 1, "government": False},
                ],
                "tech_level": 8,
                "cities": [
                    {"q": 5, "r": 0, "is_capital": True, "is_mature": False, "wonder": None, "on_fort": False},
                ],
                "control_tokens": [],
                "armies": [None],
                "caravans": [None],
                "resources": [],
                "natural_wonders": [],
                "trade_tokens_total": 2,
                "diplomacy_cards": [],
                "wonders_built": [],
                "victory_progress": {},
            },
            {
                "id": 3, "leader": "China", "government": "autocracy",
                "focus_row": [
                    {"type": "culture", "slot": 2, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "science", "slot": 1, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "economy", "slot": 4, "tech_level": 1, "trade_tokens": 0, "government": False},
                    {"type": "industry", "slot": 5, "tech_level": 2, "trade_tokens": 2, "government": True},
                    {"type": "military", "slot": 3, "tech_level": 2, "trade_tokens": 1, "government": False},
                    {"type": "growth", "slot": 1, "tech_level": 1, "trade_tokens": 0, "government": False},
                ],
                "tech_level": 10,
                "cities": [
                    {"q": -3, "r": 2, "is_capital": True, "is_mature": True, "wonder": None, "on_fort": False},
                    {"q": -4, "r": 3, "is_capital": False, "is_mature": False, "wonder": None, "on_fort": True},
                ],
                "control_tokens": [
                    {"q": -2, "r": 1, "reinforced": True, "district": "encampment"},
                    {"q": -3, "r": 3, "reinforced": True, "district": None},
                ],
                "armies": [{"q": -2, "r": 2}, {"q": -1, "r": 2}],
                "caravans": [{"q": -2, "r": 0}],
                "resources": ["diamond"],
                "natural_wonders": ["great_barrier_reef"],
                "trade_tokens_total": 4,
                "diplomacy_cards": ["rome_card", "buenos_aires"],
                "wonders_built": [],
                "victory_progress": {"warmonger": True, "preservationist": True},
            },
        ],
        "victory_cards": [
            {"id": "vc1", "agenda_a": "populous", "agenda_b": "explorer", "is_fort_card": False},
            {"id": "vc2", "agenda_a": "warmonger", "agenda_b": "preservationist", "is_fort_card": False},
            {"id": "vc3", "agenda_a": "aesthetic", "agenda_b": "scholarly", "is_fort_card": False},
            {"id": "vc4", "agenda_a": "fortified", "agenda_b": "expeditionary", "is_fort_card": True},
            {"id": "vc5", "agenda_a": "industrious", "agenda_b": "progressive", "is_fort_card": False},
        ],
        "event_dial": 2,
        "turn_number": 12,
        "barbarians": [{"q": 2, "r": -1}],
    }


# ---------------------------------------------------------------------------
# 1. Parse and query
# ---------------------------------------------------------------------------

class TestParseAndQuery:
    def test_player_count(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert len(state.players) == 3

    def test_tile_count(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert len(state.map_tiles) == 9

    def test_player_leader(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        assert p1 is not None
        assert p1.leader == "Rome"

    def test_player_government(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        p2 = state.get_player(2)
        assert p1.government == "democracy"
        assert p2.government is None

    def test_focus_row_length(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        assert len(p1.focus_row) == 6

    def test_focus_card_fields(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        economy_card = [fc for fc in p1.focus_row if fc.card_type == "economy"][0]
        assert economy_card.slot == 5
        assert economy_card.tech_level == 2
        assert economy_card.trade_tokens == 2
        assert economy_card.has_government is True
        assert economy_card.government_arrows == 2

    def test_government_arrows_default(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        culture_card = [fc for fc in p1.focus_row if fc.card_type == "culture"][0]
        assert culture_card.government_arrows == 0

    def test_tech_level(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert state.get_player(1).tech_level == 14
        assert state.get_player(2).tech_level == 8
        assert state.get_player(3).tech_level == 10

    def test_cities_parsed(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        assert len(p1.cities) == 2
        capital = [c for c in p1.cities if c.is_capital][0]
        assert capital.coord == HexCoord(0, 0)
        assert capital.wonder == "colosseum"

    def test_control_tokens_parsed(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        assert len(p1.control_tokens) == 2
        campus = [ct for ct in p1.control_tokens if ct.district_type == "campus"][0]
        assert campus.coord == HexCoord(0, 1)
        assert campus.reinforced is False

    def test_armies_with_none(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        assert len(p1.armies) == 2
        on_map = [a for a in p1.armies if a.coord is not None]
        on_card = [a for a in p1.armies if a.coord is None]
        assert len(on_map) == 1
        assert len(on_card) == 1
        assert on_map[0].coord == HexCoord(2, 0)

    def test_caravans_with_none(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        assert len(p1.caravans) == 2
        on_map = [c for c in p1.caravans if c.coord is not None]
        assert len(on_map) == 1
        assert on_map[0].coord == HexCoord(3, -1)

    def test_resources(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert state.get_player(1).resources == ("marble", "oil")
        assert state.get_player(2).resources == ()
        assert state.get_player(3).resources == ("diamond",)

    def test_victory_progress(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        p1 = state.get_player(1)
        assert p1.victory_progress == {"populous": True, "explorer": False}

    def test_victory_cards(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert len(state.victory_cards) == 5
        fort_cards = [vc for vc in state.victory_cards if vc.is_fort_card]
        assert len(fort_cards) == 1
        assert fort_cards[0].card_id == "vc4"

    def test_event_dial_and_turn(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert state.event_dial_position == 2
        assert state.turn_number == 12

    def test_barbarian_positions(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert len(state.barbarian_positions) == 1
        assert state.barbarian_positions[0] == HexCoord(2, -1)

    def test_tile_terrain_and_resource(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        hills = state.get_tile(1, 0)
        assert hills is not None
        assert hills.terrain == "hills"
        assert hills.has_resource == "marble"

    def test_tile_natural_wonder(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        mountain = state.get_tile(-1, 0)
        assert mountain.has_natural_wonder == "great_barrier_reef"

    def test_tile_city_state(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        tile = state.get_tile(0, -1)
        assert tile.has_city_state == "buenos_aires"

    def test_tile_barbarian(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        tile = state.get_tile(2, -1)
        assert tile.has_barbarian is True

    def test_tile_fort(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        tile = state.get_tile(3, 0)
        assert tile.has_fort is True

    def test_get_tile_missing(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert state.get_tile(100, 100) is None

    def test_get_player_missing(self):
        state = CivGameState.from_game_data(make_sample_game_data())
        assert state.get_player(99) is None


# ---------------------------------------------------------------------------
# 2. Friendly spaces
# ---------------------------------------------------------------------------

class TestFriendlySpaces:
    def test_player1_friendly_spaces(self):
        """Player 1 has 2 cities + 2 control tokens = 4 friendly spaces."""
        state = CivGameState.from_game_data(make_sample_game_data())
        spaces = state.friendly_spaces(1)
        assert len(spaces) == 4
        # Cities at (0,0) and (-1,1); tokens at (1,0) and (0,1)
        assert (0, 0) in spaces
        assert (-1, 1) in spaces
        assert (1, 0) in spaces
        assert (0, 1) in spaces

    def test_player2_friendly_spaces(self):
        """Player 2 has 1 city, 0 tokens = 1 friendly space."""
        state = CivGameState.from_game_data(make_sample_game_data())
        spaces = state.friendly_spaces(2)
        assert len(spaces) == 1
        assert (5, 0) in spaces

    def test_player3_friendly_spaces(self):
        """Player 3 has 2 cities + 2 control tokens = 4 friendly spaces."""
        state = CivGameState.from_game_data(make_sample_game_data())
        spaces = state.friendly_spaces(3)
        assert len(spaces) == 4
        assert (-3, 2) in spaces
        assert (-4, 3) in spaces
        assert (-2, 1) in spaces
        assert (-3, 3) in spaces

    def test_nonexistent_player(self):
        """Missing player returns empty set."""
        state = CivGameState.from_game_data(make_sample_game_data())
        assert state.friendly_spaces(99) == set()


# ---------------------------------------------------------------------------
# 3. City maturity check
# ---------------------------------------------------------------------------

class TestCityMaturity:
    def test_capital_rome_neighbors(self):
        """Rome's capital at (0,0) - check is_city_mature against the map.

        Neighbors of (0,0): (1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)
        Friendly to P1: (1,0) token, (0,1) token, (-1,1) city
        Water: (1,-1)
        Not friendly: (0,-1) city_state tile, (-1,0) mountain tile
        So NOT mature by the game logic (unfriendly neighbors exist).
        """
        state = CivGameState.from_game_data(make_sample_game_data())
        capital = state.get_player(1).cities[0]
        assert capital.is_capital is True
        # (0,-1) and (-1,0) are not friendly/water, so maturity check fails
        assert state.is_city_mature(capital) is False

    def test_egypt_capital_off_map_neighbors(self):
        """Egypt's capital at (5,0) - most neighbors are off-map.

        Neighbors of (5,0): (6,0), (6,-1), (5,-1), (4,0), (4,1), (5,1)
        None of these are in the sample map, so they are off-map.
        Off-map hexes are treated as non-friendly -> NOT mature.
        """
        state = CivGameState.from_game_data(make_sample_game_data())
        capital = state.get_player(2).cities[0]
        assert state.is_city_mature(capital) is False


# ---------------------------------------------------------------------------
# 4. Hex map integration with state coordinates
# ---------------------------------------------------------------------------

class TestHexMapIntegration:
    def test_hex_neighbors_of_origin(self):
        neighbors = hex_neighbors(0, 0)
        assert len(neighbors) == 6
        expected = {(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)}
        assert set(neighbors) == expected

    def test_hex_distance_adjacent(self):
        """Adjacent tiles should be distance 1."""
        assert hex_distance(0, 0, 1, 0) == 1
        assert hex_distance(0, 0, 0, 1) == 1
        assert hex_distance(0, 0, -1, 1) == 1

    def test_hex_distance_same(self):
        assert hex_distance(0, 0, 0, 0) == 0

    def test_hex_distance_two_apart(self):
        """(0,0) to (2,-1) should be distance 2."""
        assert hex_distance(0, 0, 2, -1) == 2

    def test_hex_distance_between_state_cities(self):
        """Distance from Rome's capital (0,0) to China's capital (-3,2)."""
        d = hex_distance(0, 0, -3, 2)
        assert d == 3

    def test_neighbors_match_map_adjacency(self):
        """Verify that map tiles adjacent to (0,0) appear in hex_neighbors."""
        state = CivGameState.from_game_data(make_sample_game_data())
        origin_neighbors = set(hex_neighbors(0, 0))
        # All these tiles exist in the map and are neighbors of (0,0)
        for coord in [(1, 0), (0, 1), (-1, 1), (1, -1), (-1, 0), (0, -1)]:
            assert coord in origin_neighbors
            assert state.get_tile(*coord) is not None


# ---------------------------------------------------------------------------
# 5. Multiplayer handler integration
# ---------------------------------------------------------------------------

class TestMultiplayerHandlerIntegration:
    def test_three_player_strength(self):
        """compute_player_strength with mock 3-player history."""
        history = [
            MomentumPoint(move_number=1, eval_score=0.1, delta=0.05, player_who_moved=1),
            MomentumPoint(move_number=2, eval_score=0.15, delta=0.05, player_who_moved=2),
            MomentumPoint(move_number=3, eval_score=0.3, delta=0.25, player_who_moved=3),
            MomentumPoint(move_number=4, eval_score=0.25, delta=-0.05, player_who_moved=1),
            MomentumPoint(move_number=5, eval_score=0.2, delta=-0.05, player_who_moved=2),
            MomentumPoint(move_number=6, eval_score=0.1, delta=-0.10, player_who_moved=3),
        ]
        strength = compute_player_strength(history, player_count=3)

        assert set(strength.players.keys()) == {"p1", "p2", "p3"}
        # p1: 2 moves, both delta < 0.15 -> 100%
        assert strength.players["p1"] == 100.0
        # p2: 2 moves, both delta < 0.15 -> 100%
        assert strength.players["p2"] == 100.0
        # p3: 2 moves, move 3 delta=0.25 bad, move 6 delta=0.10 good -> 50%
        assert strength.players["p3"] == 50.0

    def test_three_player_momentum(self):
        """compute_momentum works with 3-player history."""
        history = [
            MomentumPoint(move_number=1, eval_score=0.1, delta=0.1, player_who_moved=1),
            MomentumPoint(move_number=2, eval_score=0.0, delta=-0.1, player_who_moved=2),
            MomentumPoint(move_number=3, eval_score=0.2, delta=0.2, player_who_moved=3),
        ]
        momentum = compute_momentum(history)
        assert momentum.current == 0.2
        assert len(momentum.history) == 3

    def test_board_state_message_with_game_data(self):
        """BoardStateMessage accepts player_count=3 and game_data dict."""
        msg = BoardStateMessage(
            game="civilization",
            move_number=12,
            player_to_move=1,
            player_count=3,
            game_data=make_sample_game_data(),
        )
        assert msg.player_count == 3
        assert msg.game_data is not None
        assert len(msg.game_data["players"]) == 3

    def test_game_data_round_trip(self):
        """game_data -> CivGameState -> verify fields match message."""
        data = make_sample_game_data()
        msg = BoardStateMessage(
            game="civilization",
            move_number=12,
            player_to_move=1,
            player_count=3,
            game_data=data,
        )
        state = CivGameState.from_game_data(msg.game_data)
        assert len(state.players) == msg.player_count
        assert state.turn_number == data["turn_number"]


# ---------------------------------------------------------------------------
# 6. Connect Four regression
# ---------------------------------------------------------------------------

class TestConnectFourRegression:
    def test_connect_four_message_no_game_data(self):
        """Standard Connect Four message has no game_data and player_count=2."""
        msg = BoardStateMessage(
            game="connect4",
            board=[[0] * 7 for _ in range(6)],
            rows=6,
            cols=7,
            move_number=0,
            player_to_move=1,
        )
        assert msg.player_count == 2
        assert msg.game_data is None
        assert len(msg.board) == 6
        assert len(msg.board[0]) == 7

    def test_player_strength_has_p1_p2(self):
        """PlayerStrength still has p1/p2 fields for 2-player games."""
        history = [
            MomentumPoint(move_number=1, eval_score=0.1, delta=0.05, player_who_moved=1),
            MomentumPoint(move_number=2, eval_score=0.0, delta=-0.10, player_who_moved=2),
        ]
        strength = compute_player_strength(history, player_count=2)
        assert hasattr(strength, "p1")
        assert hasattr(strength, "p2")
        assert 0 <= strength.p1 <= 100
        assert 0 <= strength.p2 <= 100
        assert strength.players["p1"] == strength.p1
        assert strength.players["p2"] == strength.p2

    def test_connect_four_board_preserved(self):
        """Board grid is preserved correctly for Connect Four messages."""
        board = [[0] * 7 for _ in range(6)]
        board[5][3] = 1
        board[5][0] = 2
        msg = BoardStateMessage(
            game="connect4",
            board=board,
            rows=6,
            cols=7,
            move_number=2,
            player_to_move=1,
        )
        assert msg.board[5][3] == 1
        assert msg.board[5][0] == 2
        assert msg.board[0][0] == 0


# ---------------------------------------------------------------------------
# 7. Empty game_data
# ---------------------------------------------------------------------------

class TestEmptyGameData:
    def test_empty_dict_no_crash(self):
        """CivGameState.from_game_data({}) produces valid empty state."""
        state = CivGameState.from_game_data({})
        assert len(state.map_tiles) == 0
        assert len(state.players) == 0
        assert state.turn_number == 0
        assert state.event_dial_position == 0
        assert len(state.victory_cards) == 0
        assert len(state.barbarian_positions) == 0

    def test_empty_players_list(self):
        state = CivGameState.from_game_data({"players": []})
        assert len(state.players) == 0

    def test_empty_map(self):
        state = CivGameState.from_game_data({"map": []})
        assert len(state.map_tiles) == 0

    def test_partial_player(self):
        """A player with only an id still parses without errors."""
        state = CivGameState.from_game_data({"players": [{"id": 1}]})
        assert len(state.players) == 1
        p = state.get_player(1)
        assert p.leader == ""
        assert p.government is None
        assert len(p.focus_row) == 0
        assert len(p.cities) == 0

    def test_partial_tile(self):
        """A tile with only coordinates still parses with defaults."""
        state = CivGameState.from_game_data({"map": [{"q": 5, "r": 5}]})
        tile = state.get_tile(5, 5)
        assert tile is not None
        assert tile.terrain == "grassland"
        assert tile.has_resource is None
        assert tile.has_barbarian is False

    def test_friendly_spaces_empty_state(self):
        state = CivGameState.from_game_data({})
        assert state.friendly_spaces(1) == set()


# ---------------------------------------------------------------------------
# 8. Schema backwards compatibility
# ---------------------------------------------------------------------------

class TestSchemaBackwardsCompat:
    def test_minimal_board_state_message(self):
        """BoardStateMessage with only original required fields defaults correctly."""
        msg = BoardStateMessage(
            game="connect4",
            move_number=0,
            player_to_move=1,
        )
        assert msg.player_count == 2
        assert msg.game_data is None
        assert msg.board == []
        assert msg.rows == 0
        assert msg.cols == 0
        assert msg.source == "bga"
        assert msg.type == "board_state"

    def test_player_strength_defaults(self):
        """PlayerStrength defaults work for both old and new fields."""
        strength = PlayerStrength()
        assert strength.p1 == 50.0
        assert strength.p2 == 50.0
        assert strength.players == {}

    def test_board_state_accepts_game_data(self):
        """New game_data field can be set without affecting other defaults."""
        msg = BoardStateMessage(
            game="civilization",
            move_number=5,
            player_to_move=2,
            game_data={"map": [], "players": []},
        )
        assert msg.game_data is not None
        assert msg.board == []
        assert msg.player_count == 2  # still defaults to 2

    def test_board_state_accepts_player_count(self):
        """player_count can be set to values other than 2."""
        for pc in [1, 2, 3, 4, 5]:
            msg = BoardStateMessage(
                game="test",
                move_number=0,
                player_to_move=1,
                player_count=pc,
            )
            assert msg.player_count == pc

    def test_board_state_serialization_round_trip(self):
        """BoardStateMessage can serialize and deserialize with new fields."""
        original = BoardStateMessage(
            game="civilization",
            move_number=10,
            player_to_move=2,
            player_count=3,
            game_data=make_sample_game_data(),
        )
        dumped = original.model_dump()
        restored = BoardStateMessage(**dumped)
        assert restored.game == "civilization"
        assert restored.player_count == 3
        assert restored.game_data is not None
        assert len(restored.game_data["players"]) == 3


# ---------------------------------------------------------------------------
# 9. v2 evaluator integration
# ---------------------------------------------------------------------------

class TestV2EvaluatorIntegration:
    def test_all_players_score_positive(self):
        """Players with pieces should get positive scores from v2 evaluator."""
        from app.engine.civilization.evaluator import evaluate_position

        state = CivGameState.from_game_data(make_sample_game_data())
        scores = evaluate_position(state)
        assert len(scores) == 3
        assert scores[1] > 0
        assert scores[2] > 0
        assert scores[3] > 0

    def test_stronger_player_wins(self):
        """Player 1 (most pieces/wonders/tech) should score highest."""
        from app.engine.civilization.evaluator import evaluate_position

        state = CivGameState.from_game_data(make_sample_game_data())
        scores = evaluate_position(state)
        assert scores[1] > scores[2]

    def test_analyzer_entry_point(self):
        """The analyzer produces a valid EngineResult."""
        from app.engine.civilization.analyzer import analyze_civ_position

        result = analyze_civ_position(
            game_data=make_sample_game_data(),
            move_number=12,
            player_to_move=1,
        )
        assert result.engine_used == "handcoded"
        assert result.depth_reached == 1
        assert isinstance(result.raw_score, float)
