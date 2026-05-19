"""Heuristic evaluator v2 for Civilization: A New Dawn.

Thirteen scoring functions assess each player's position across key dimensions.
The main entry point is ``evaluate_position`` which returns a total score per player.
"""

from __future__ import annotations

from app.engine.civilization.hex_map import hex_distance, hex_neighbors
from app.engine.civilization.state import CivGameState, PlayerState


# ---------------------------------------------------------------------------
# Wonder era data
# ---------------------------------------------------------------------------

WONDER_ERA: dict[str, int] = {
    "stonehenge": 1, "pyramids": 1, "colosseum": 1, "great_library": 1,
    "great_lighthouse": 1, "oracle": 1, "hanging_gardens": 1, "terracotta_army": 1,
    "alhambra": 2, "forbidden_city": 2, "chichen_itza": 2, "hagia_sophia": 2,
    "machu_picchu": 2, "notre_dame": 2, "porcelain_tower": 2, "venetian_arsenal": 2,
    "broadway": 3, "eiffel_tower": 3, "sydney_opera_house": 3, "big_ben": 3,
    "ruhr_valley": 3, "cristo_redentor": 3, "pentagon": 3, "oxford_university": 3,
}

WONDER_ERA_SCORES = {1: 10, 2: 18, 3: 25}
WONDER_DEFAULT_SCORE = 15


# ---------------------------------------------------------------------------
# Agenda progress measurement
# ---------------------------------------------------------------------------

AGENDA_TARGETS: dict[str, tuple[str, int]] = {
    "money_grubber": ("city_count", 8),
    "populous": ("mature_city_count", 5),
    "explorer": ("water_edge_spaces", 15),
    "scholarly": ("tech_level", 24),
    "preservationist": ("natural_wonder_count", 2),
    "defensive": ("reinforced_token_count", 15),
    "expansionist": ("city_tile_diversity", 6),
    "provincial": ("mature_city_tile_diversity", 4),
    "diversified": ("wonder_type_diversity", 3),
    "industrious": ("district_count", 5),
    "diplomatic": ("diplomacy_source_count", 4),
    "fortified": ("fort_count", 1),
    "expeditionary": ("fort_count", 2),
    "progressive": ("tech_level_4_cards", 3),
    "aesthetic": ("cultural_wonder_count", 2),
    "warmonger": ("military_wonder_count", 2),
    "technophile": ("scientific_wonder_count", 2),
    "civilized": ("economic_wonder_count", 2),
    "hoarder": ("resource_count", 5),
    "prolific": ("same_era_wonder_count", 2),
    "devastating": ("max_combat_potential", 16),
}


def _measure_agenda_progress(
    agenda: str, player: PlayerState, state: CivGameState,
) -> float:
    target = AGENDA_TARGETS.get(agenda.lower())
    if target is None:
        return 0.0

    measure_type, target_count = target

    if measure_type == "city_count":
        current = len(player.cities)
    elif measure_type == "mature_city_count":
        current = sum(1 for c in player.cities if c.is_mature)
    elif measure_type == "tech_level":
        current = player.tech_level
    elif measure_type == "natural_wonder_count":
        current = len(player.natural_wonders)
    elif measure_type == "reinforced_token_count":
        current = sum(1 for ct in player.control_tokens if ct.reinforced)
    elif measure_type == "district_count":
        current = sum(1 for ct in player.control_tokens if ct.district_type)
    elif measure_type == "diplomacy_source_count":
        current = len(player.diplomacy_cards)
    elif measure_type == "fort_count":
        current = sum(1 for c in player.cities if c.on_fort)
    elif measure_type == "tech_level_4_cards":
        current = sum(1 for fc in player.focus_row if fc.tech_level == 4)
    elif measure_type == "resource_count":
        current = len(player.resources) + len(player.natural_wonders)
    elif measure_type == "wonder_type_diversity":
        types = set()
        for w in player.wonders_built:
            era = WONDER_ERA.get(w.lower(), 0)
            if era:
                types.add(era)
        current = len(types)
    elif measure_type == "city_tile_diversity":
        current = len({(c.coord.q // 4, c.coord.r // 4) for c in player.cities})
    elif measure_type == "mature_city_tile_diversity":
        current = len({
            (c.coord.q // 4, c.coord.r // 4) for c in player.cities if c.is_mature
        })
    elif measure_type == "water_edge_spaces":
        all_map = set(state.map_tiles.keys())
        friendly = state.friendly_spaces(player.player_id)
        current = 0
        for q, r in friendly:
            tile = state.get_tile(q, r)
            if tile and tile.terrain == "water":
                current += 1
                continue
            for nq, nr in hex_neighbors(q, r):
                ntile = state.get_tile(nq, nr)
                if ntile and ntile.terrain == "water":
                    current += 1
                    break
                elif (nq, nr) not in all_map:
                    current += 1
                    break
    elif measure_type == "same_era_wonder_count":
        era_counts: dict[int, int] = {}
        for w in player.wonders_built:
            era = WONDER_ERA.get(w.lower(), 0)
            if era:
                era_counts[era] = era_counts.get(era, 0) + 1
        current = max(era_counts.values()) if era_counts else 0
    elif measure_type in (
        "cultural_wonder_count", "military_wonder_count",
        "scientific_wonder_count", "economic_wonder_count",
    ):
        current = len(player.wonders_built)
    elif measure_type == "max_combat_potential":
        mil_cards = [fc for fc in player.focus_row if fc.card_type == "military"]
        slot_val = max((mc.slot for mc in mil_cards), default=0)
        current = slot_val + 6 + sum(mc.trade_tokens for mc in mil_cards)
    else:
        return 0.0

    if target_count <= 0:
        return 0.0
    return min(current / target_count, 1.0)


# ---------------------------------------------------------------------------
# 1. Victory progress  (max ~400)
# ---------------------------------------------------------------------------

def score_victory_progress(player: PlayerState, state: CivGameState) -> float:
    completed = sum(1 for v in player.victory_progress.values() if v)
    score = completed * 75.0

    active_agendas: set[str] = set()
    for vc in state.victory_cards:
        if vc.agenda_a:
            active_agendas.add(vc.agenda_a)
        if vc.agenda_b:
            active_agendas.add(vc.agenda_b)

    for agenda in active_agendas:
        if player.victory_progress.get(agenda, False):
            continue
        progress = _measure_agenda_progress(agenda, player, state)
        score += progress * 30.0

    if completed >= 3:
        score += 50.0
    if completed >= 4:
        score += 75.0
    return min(score, 400.0)


# ---------------------------------------------------------------------------
# 2. Territory  (max ~140)
# ---------------------------------------------------------------------------

def score_territory(player: PlayerState, state: CivGameState) -> float:
    friendly = state.friendly_spaces(player.player_id)
    score = len(friendly) * 2.0
    for q, r in friendly:
        tile = state.get_tile(q, r)
        if tile is not None:
            if tile.has_resource:
                score += 5.0
            if tile.has_natural_wonder:
                score += 8.0

    components = state.territory_components(player.player_id)
    if components:
        largest = max(len(c) for c in components)
        score += largest * 0.5

    for q, r in friendly:
        for nq, nr in hex_neighbors(q, r):
            tile = state.get_tile(nq, nr)
            if tile and not tile.explored:
                score += 1.5
                break

    return min(score, 140.0)


# ---------------------------------------------------------------------------
# 3. Cities  (max ~150)
# ---------------------------------------------------------------------------

def score_cities(player: PlayerState, state: CivGameState) -> float:
    score = len(player.cities) * 15.0
    for city in player.cities:
        if city.is_mature:
            score += 10.0
        if city.wonder:
            score += 8.0
        if city.on_fort:
            score += 12.0
        if city.is_capital:
            score += 5.0
    return min(score, 150.0)


# ---------------------------------------------------------------------------
# 4. Tech  (max ~100)
# ---------------------------------------------------------------------------

def score_tech(player: PlayerState, state: CivGameState) -> float:
    score = player.tech_level * 4.0
    for card in player.focus_row:
        if card.tech_level == 4:
            score += 10.0
        elif card.tech_level == 3:
            score += 5.0
    return min(score, 100.0)


# ---------------------------------------------------------------------------
# 5. Military  (max ~100)
# ---------------------------------------------------------------------------

def score_military(player: PlayerState, state: CivGameState) -> float:
    deployed_armies = [a for a in player.armies if a.coord is not None]
    score = len(deployed_armies) * 15.0

    reinforced = sum(1 for ct in player.control_tokens if ct.reinforced)
    score += reinforced * 3.0

    fort_cities = sum(1 for c in player.cities if c.on_fort)
    score += fort_cities * 15.0

    encampments = sum(1 for ct in player.control_tokens if ct.district_type == "encampment")
    score += encampments * 5.0

    opponent_cities = state.all_opponent_cities(player.player_id)
    for army in deployed_armies:
        if army.coord is None:
            continue
        for oc in opponent_cities:
            d = hex_distance(army.coord.q, army.coord.r, oc.coord.q, oc.coord.r)
            if d <= 3:
                score += max(0, 4 - d) * 2.0
                break
        for barb in state.barbarian_positions:
            d = hex_distance(army.coord.q, army.coord.r, barb.q, barb.r)
            if d <= 2:
                score += 3.0
                break

    mil_cards = [fc for fc in player.focus_row if fc.card_type == "military"]
    for mc in mil_cards:
        if mc.slot >= 4:
            score += 5.0

    return min(score, 100.0)


# ---------------------------------------------------------------------------
# 6. Economy  (max ~90)
# ---------------------------------------------------------------------------

def score_economy(player: PlayerState, state: CivGameState) -> float:
    score = player.trade_tokens_total * 3.0
    active_caravans = [c for c in player.caravans if c.coord is not None]
    score += len(active_caravans) * 10.0
    mature_cities = sum(1 for c in player.cities if c.is_mature)
    score += mature_cities * 5.0
    hubs = sum(1 for ct in player.control_tokens if ct.district_type == "commercial_hub")
    score += hubs * 5.0

    for caravan in active_caravans:
        if caravan.coord is None:
            continue
        for (q, r), tile in state.map_tiles.items():
            if tile.has_city_state:
                d = hex_distance(caravan.coord.q, caravan.coord.r, q, r)
                if d <= 3:
                    score += max(0, 4 - d) * 2.0
                    break
        for oc in state.all_opponent_cities(player.player_id):
            d = hex_distance(caravan.coord.q, caravan.coord.r, oc.coord.q, oc.coord.r)
            if d <= 3:
                score += max(0, 4 - d) * 1.5
                break

    return min(score, 90.0)


# ---------------------------------------------------------------------------
# 7. Wonders  (max ~90)
# ---------------------------------------------------------------------------

def score_wonders(player: PlayerState, state: CivGameState) -> float:
    score = 0.0
    for w in player.wonders_built:
        era = WONDER_ERA.get(w.lower(), 0)
        score += WONDER_ERA_SCORES.get(era, WONDER_DEFAULT_SCORE)

    count = len(player.wonders_built)
    if count >= 3:
        score += 10.0
    if count >= 5:
        score += 10.0
    return min(score, 90.0)


# ---------------------------------------------------------------------------
# 8. Focus row  (max ~70)
# ---------------------------------------------------------------------------

def score_focus_row(player: PlayerState) -> float:
    score = 0.0
    for card in player.focus_row:
        effective_slot = min(card.slot + card.government_arrows, 5)

        if effective_slot >= 5:
            score += 10.0
        elif effective_slot >= 4:
            score += 6.0
        elif effective_slot >= 3:
            score += 3.0
        elif effective_slot >= 2:
            score += 1.0

        if card.has_government:
            score += 3.0
            score += card.government_arrows * 2.0

        score += card.trade_tokens
    return min(score, 70.0)


# ---------------------------------------------------------------------------
# 9. Diplomacy  (max ~50)
# ---------------------------------------------------------------------------

def score_diplomacy(player: PlayerState, state: CivGameState) -> float:
    count = len(player.diplomacy_cards)
    score = count * 8.0
    if count >= 3:
        score += 10.0
    if count >= 5:
        score += 10.0
    return min(score, 50.0)


# ---------------------------------------------------------------------------
# 10. Districts  (max ~80)  [NEW in v2]
# ---------------------------------------------------------------------------

def score_districts(player: PlayerState, state: CivGameState) -> float:
    score = 0.0
    districts = [ct for ct in player.control_tokens if ct.district_type]

    district_types = {ct.district_type for ct in districts}
    score += len(district_types) * 4.0

    for ct in districts:
        adj_tiles = state.tiles_adjacent_to(ct.coord.q, ct.coord.r)

        if ct.district_type == "campus":
            for tile in adj_tiles:
                if tile.terrain == "mountain":
                    score += 4.0
                if tile.has_natural_wonder:
                    score += 6.0

        elif ct.district_type == "commercial_hub":
            for tile in adj_tiles:
                if tile.terrain == "desert":
                    score += 3.0
            for city in player.cities:
                d = hex_distance(ct.coord.q, ct.coord.r, city.coord.q, city.coord.r)
                if d <= 2 and city.is_mature:
                    score += 4.0

        elif ct.district_type == "encampment":
            for oc in state.all_opponent_cities(player.player_id):
                d = hex_distance(ct.coord.q, ct.coord.r, oc.coord.q, oc.coord.r)
                if d <= 3:
                    score += max(0, 4 - d) * 2.0
                    break
            for barb in state.barbarian_positions:
                d = hex_distance(ct.coord.q, ct.coord.r, barb.q, barb.r)
                if d <= 2:
                    score += 3.0
                    break

        elif ct.district_type == "industrial_zone":
            for tile in adj_tiles:
                if tile.terrain == "forest":
                    score += 4.0

        elif ct.district_type == "theater_square":
            for city in player.cities:
                if city.wonder:
                    d = hex_distance(ct.coord.q, ct.coord.r, city.coord.q, city.coord.r)
                    if d <= 2:
                        score += 5.0
                        break

    return min(score, 80.0)


# ---------------------------------------------------------------------------
# 11. Resources  (max ~50)  [NEW in v2]
# ---------------------------------------------------------------------------

def score_resources(player: PlayerState, state: CivGameState) -> float:
    score = len(player.resources) * 5.0
    unique_resources = set(player.resources)
    score += len(unique_resources) * 3.0
    score += len(player.natural_wonders) * 8.0

    if len(unique_resources) >= 4:
        score += 8.0
    elif len(unique_resources) >= 3:
        score += 4.0

    return min(score, 50.0)


# ---------------------------------------------------------------------------
# 12. Forts  (max ~40)  [NEW in v2]
# ---------------------------------------------------------------------------

def score_forts(player: PlayerState, state: CivGameState) -> float:
    score = 0.0
    fort_cities = [c for c in player.cities if c.on_fort]
    fort_count = len(fort_cities)
    score += fort_count * 12.0

    fort_cards = [vc for vc in state.victory_cards if vc.is_fort_card]
    if fort_cards and fort_count > 0:
        score += 8.0

    friendly = state.friendly_spaces(player.player_id)
    for (q, r), tile in state.map_tiles.items():
        if tile.has_fort and (q, r) not in friendly:
            claimed = False
            for p in state.players:
                if p.player_id == player.player_id:
                    continue
                if any(c.on_fort and c.coord.q == q and c.coord.r == r for c in p.cities):
                    claimed = True
                    break
            if not claimed:
                for city in player.cities:
                    d = hex_distance(city.coord.q, city.coord.r, q, r)
                    if d <= 4:
                        score += max(0, 5 - d) * 2.0
                        break

    return min(score, 40.0)


# ---------------------------------------------------------------------------
# 13. Position  (max ~60)  [NEW in v2]
# ---------------------------------------------------------------------------

def score_position(player: PlayerState, state: CivGameState) -> float:
    score = 0.0
    friendly = state.friendly_spaces(player.player_id)
    all_map_coords = set(state.map_tiles.keys())

    for city in player.cities:
        neighbors_on_map = sum(
            1 for nq, nr in hex_neighbors(city.coord.q, city.coord.r)
            if (nq, nr) in all_map_coords
        )
        if neighbors_on_map < 6:
            score += (6 - neighbors_on_map) * 2.0

    components = state.territory_components(player.player_id)
    if components and len(friendly) > 0:
        largest = max(len(c) for c in components)
        score += (largest / len(friendly)) * 15.0

    opponent_spaces: set[tuple[int, int]] = set()
    for p in state.players:
        if p.player_id != player.player_id:
            opponent_spaces |= state.friendly_spaces(p.player_id)

    frontier_count = 0
    for q, r in friendly:
        for nq, nr in hex_neighbors(q, r):
            if (nq, nr) in opponent_spaces:
                frontier_count += 1
                break
    score += min(frontier_count * 1.5, 15.0)

    if player.cities:
        city_qs = [c.coord.q for c in player.cities]
        city_rs = [c.coord.r for c in player.cities]
        q_spread = max(city_qs) - min(city_qs) if len(city_qs) > 1 else 0
        r_spread = max(city_rs) - min(city_rs) if len(city_rs) > 1 else 0
        score += min((q_spread + r_spread) * 1.0, 10.0)

    return min(score, 60.0)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def evaluate_position(state: CivGameState) -> dict[int, float]:
    """Return a heuristic score for every player in *state*."""
    scores: dict[int, float] = {}
    for player in state.players:
        scores[player.player_id] = (
            score_victory_progress(player, state)
            + score_territory(player, state)
            + score_cities(player, state)
            + score_tech(player, state)
            + score_military(player, state)
            + score_economy(player, state)
            + score_wonders(player, state)
            + score_focus_row(player)
            + score_diplomacy(player, state)
            + score_districts(player, state)
            + score_resources(player, state)
            + score_forts(player, state)
            + score_position(player, state)
        )
    return scores
