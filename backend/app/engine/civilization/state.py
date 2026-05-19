"""Typed game-state model and parser for Civilization: A New Dawn."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from app.engine.civilization.hex_map import hex_neighbors


# ---------------------------------------------------------------------------
# Coordinate & map primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HexCoord:
    q: int  # axial column
    r: int  # axial row


@dataclass(frozen=True)
class MapTile:
    coord: HexCoord
    terrain: str  # "grassland"|"hills"|"forest"|"desert"|"mountain"|"water"
    has_resource: str | None = None  # "marble"|"mercury"|"oil"|"diamond"
    has_natural_wonder: str | None = None
    has_barbarian: bool = False
    has_city_state: str | None = None
    has_fort: bool = False
    explored: bool = True


# ---------------------------------------------------------------------------
# Player pieces
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class City:
    coord: HexCoord
    owner: int  # player number (1-5)
    is_capital: bool = False
    is_mature: bool = False
    wonder: str | None = None
    on_fort: bool = False


@dataclass(frozen=True)
class ControlToken:
    coord: HexCoord
    owner: int
    reinforced: bool = False
    district_type: str | None = None  # None=regular, else district name


@dataclass(frozen=True)
class Army:
    coord: HexCoord | None  # None = on military card
    owner: int


@dataclass(frozen=True)
class Caravan:
    coord: HexCoord | None  # None = on economy card
    owner: int


@dataclass(frozen=True)
class FocusCard:
    card_type: str  # "culture"|"science"|"economy"|"industry"|"military"|"growth"
    slot: int  # 1-5
    tech_level: int = 1  # I=1, II=2, III=3, IV=4
    trade_tokens: int = 0  # 0-3
    has_government: bool = False
    government_arrows: int = 0


# ---------------------------------------------------------------------------
# Per-player aggregate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlayerState:
    player_id: int
    leader: str = ""
    government: str | None = None
    focus_row: tuple[FocusCard, ...] = ()
    tech_level: int = 0
    cities: tuple[City, ...] = ()
    control_tokens: tuple[ControlToken, ...] = ()
    armies: tuple[Army, ...] = ()
    caravans: tuple[Caravan, ...] = ()
    resources: tuple[str, ...] = ()
    natural_wonders: tuple[str, ...] = ()
    trade_tokens_total: int = 0
    diplomacy_cards: tuple[str, ...] = ()
    wonders_built: tuple[str, ...] = ()
    victory_progress: dict[str, bool] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Victory & global state
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VictoryCard:
    card_id: str
    agenda_a: str = ""
    agenda_b: str = ""
    is_fort_card: bool = False


@dataclass(frozen=True)
class CivGameState:
    map_tiles: dict[tuple[int, int], MapTile]  # (q, r) -> tile
    players: tuple[PlayerState, ...]
    current_player: int
    move_number: int = 0
    victory_cards: tuple[VictoryCard, ...] = ()
    event_dial_position: int = 0
    turn_number: int = 0
    barbarian_positions: tuple[HexCoord, ...] = ()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_player(self, player_id: int) -> PlayerState | None:
        """Find player by ID."""
        for p in self.players:
            if p.player_id == player_id:
                return p
        return None

    def get_tile(self, q: int, r: int) -> MapTile | None:
        """Get tile at coordinates."""
        return self.map_tiles.get((q, r))

    def friendly_spaces(self, player_id: int) -> set[tuple[int, int]]:
        """All hexes with player's control tokens or cities."""
        player = self.get_player(player_id)
        if player is None:
            return set()
        spaces: set[tuple[int, int]] = set()
        for ct in player.control_tokens:
            spaces.add((ct.coord.q, ct.coord.r))
        for city in player.cities:
            spaces.add((city.coord.q, city.coord.r))
        return spaces

    def is_city_mature(self, city: City) -> bool:
        """True if all adjacent hexes are friendly to city.owner or water."""
        friendly = self.friendly_spaces(city.owner)
        for nq, nr in hex_neighbors(city.coord.q, city.coord.r):
            if (nq, nr) in friendly:
                continue
            tile = self.get_tile(nq, nr)
            if tile is not None and tile.terrain == "water":
                continue
            # Hex is either not on the map or not friendly/water
            # Off-map hexes are treated as non-friendly
            return False
        return True

    def all_opponent_cities(self, player_id: int) -> list[City]:
        """All cities belonging to other players."""
        result: list[City] = []
        for p in self.players:
            if p.player_id != player_id:
                result.extend(p.cities)
        return result

    def tiles_adjacent_to(self, q: int, r: int) -> list[MapTile]:
        """Return MapTile objects for all valid neighbors of (q, r)."""
        result: list[MapTile] = []
        for nq, nr in hex_neighbors(q, r):
            tile = self.get_tile(nq, nr)
            if tile is not None:
                result.append(tile)
        return result

    def territory_components(self, player_id: int) -> list[set[tuple[int, int]]]:
        """Connected components of a player's friendly spaces."""
        from app.engine.civilization.hex_map import connected_components
        return connected_components(self.friendly_spaces(player_id))

    # ------------------------------------------------------------------
    # Parser
    # ------------------------------------------------------------------

    @classmethod
    def from_game_data(cls, data: dict) -> CivGameState:
        """Parse a raw game_data dict into a fully typed CivGameState."""
        # --- map tiles ---
        map_tiles: dict[tuple[int, int], MapTile] = {}
        for raw_tile in data.get("map", []):
            q = raw_tile.get("q", 0)
            r = raw_tile.get("r", 0)
            tile = MapTile(
                coord=HexCoord(q=q, r=r),
                terrain=raw_tile.get("terrain", "grassland"),
                has_resource=raw_tile.get("resource"),
                has_natural_wonder=raw_tile.get("natural_wonder"),
                has_barbarian=raw_tile.get("barbarian", False),
                has_city_state=raw_tile.get("city_state"),
                has_fort=raw_tile.get("fort", False),
                explored=raw_tile.get("explored", True),
            )
            map_tiles[(q, r)] = tile

        # --- players ---
        players: list[PlayerState] = []
        for raw_p in data.get("players", []):
            pid = raw_p.get("id", 0)

            # focus row
            focus_cards: list[FocusCard] = []
            for raw_fc in raw_p.get("focus_row", []):
                focus_cards.append(FocusCard(
                    card_type=raw_fc.get("type", "culture"),
                    slot=raw_fc.get("slot", 1),
                    tech_level=raw_fc.get("tech_level", 1),
                    trade_tokens=raw_fc.get("trade_tokens", 0),
                    has_government=raw_fc.get("government", False),
                    government_arrows=raw_fc.get("government_arrows", raw_fc.get("arrows", 0)),
                ))

            # cities
            cities: list[City] = []
            for raw_c in raw_p.get("cities", []):
                cities.append(City(
                    coord=HexCoord(q=raw_c.get("q", 0), r=raw_c.get("r", 0)),
                    owner=pid,
                    is_capital=raw_c.get("is_capital", False),
                    is_mature=raw_c.get("is_mature", False),
                    wonder=raw_c.get("wonder"),
                    on_fort=raw_c.get("on_fort", False),
                ))

            # control tokens
            tokens: list[ControlToken] = []
            for raw_ct in raw_p.get("control_tokens", []):
                tokens.append(ControlToken(
                    coord=HexCoord(q=raw_ct.get("q", 0), r=raw_ct.get("r", 0)),
                    owner=pid,
                    reinforced=raw_ct.get("reinforced", False),
                    district_type=raw_ct.get("district"),
                ))

            # armies (null = on card)
            armies: list[Army] = []
            for raw_a in raw_p.get("armies", []):
                if raw_a is None:
                    armies.append(Army(coord=None, owner=pid))
                else:
                    armies.append(Army(
                        coord=HexCoord(q=raw_a.get("q", 0), r=raw_a.get("r", 0)),
                        owner=pid,
                    ))

            # caravans (null = on card)
            caravans: list[Caravan] = []
            for raw_cv in raw_p.get("caravans", []):
                if raw_cv is None:
                    caravans.append(Caravan(coord=None, owner=pid))
                else:
                    caravans.append(Caravan(
                        coord=HexCoord(q=raw_cv.get("q", 0), r=raw_cv.get("r", 0)),
                        owner=pid,
                    ))

            players.append(PlayerState(
                player_id=pid,
                leader=raw_p.get("leader", ""),
                government=raw_p.get("government"),
                focus_row=tuple(focus_cards),
                tech_level=raw_p.get("tech_level", 0),
                cities=tuple(cities),
                control_tokens=tuple(tokens),
                armies=tuple(armies),
                caravans=tuple(caravans),
                resources=tuple(raw_p.get("resources", [])),
                natural_wonders=tuple(raw_p.get("natural_wonders", [])),
                trade_tokens_total=raw_p.get("trade_tokens_total", 0),
                diplomacy_cards=tuple(raw_p.get("diplomacy_cards", [])),
                wonders_built=tuple(raw_p.get("wonders_built", [])),
                victory_progress=dict(raw_p.get("victory_progress", {})),
            ))

        # --- victory cards ---
        victory_cards: list[VictoryCard] = []
        for raw_vc in data.get("victory_cards", []):
            victory_cards.append(VictoryCard(
                card_id=raw_vc.get("id", ""),
                agenda_a=raw_vc.get("agenda_a", ""),
                agenda_b=raw_vc.get("agenda_b", ""),
                is_fort_card=raw_vc.get("is_fort_card", False),
            ))

        # --- barbarian positions ---
        barbs: list[HexCoord] = []
        for raw_b in data.get("barbarians", []):
            barbs.append(HexCoord(q=raw_b.get("q", 0), r=raw_b.get("r", 0)))

        return cls(
            map_tiles=map_tiles,
            players=tuple(players),
            current_player=data.get("current_player", 1),
            move_number=data.get("move_number", 0),
            victory_cards=tuple(victory_cards),
            event_dial_position=data.get("event_dial", 0),
            turn_number=data.get("turn_number", 0),
            barbarian_positions=tuple(barbs),
        )
