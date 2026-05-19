import type { BoardState } from '../../shared/types';

/**
 * BGA Civilization: A New Dawn — State Extraction
 *
 * BGA field mapping (to be confirmed after live testing):
 *
 *   gamedatas.board / .hexes / .map_hexes / .tiles  →  game_data.map
 *   gamedatas.players                                →  game_data.players
 *   gamedatas.victory_cards / .agendas               →  game_data.victory_cards
 *   gamedatas.barbarians / .barb_tokens              →  game_data.barbarians
 *   gamedatas.event_dial / .event_track              →  game_data.event_dial
 *   gamedatas.move_nbr / .turn / .turn_number        →  game_data.turn_number
 *   gamedatas.gamestate.active_player                →  player_to_move
 *   gamedatas.playerorder / .player_table_order      →  player ordering (1,2,3...)
 */

// ---------------------------------------------------------------------------
// Bridge: inject into page context to read window.gameui.gamedatas
// ---------------------------------------------------------------------------

let cachedGameData: any = null;
let listenerSetup = false;
let hasLoggedStructure = false;

function setupGameDataBridge(): void {
  if (listenerSetup) return;
  listenerSetup = true;

  window.addEventListener('__bga_civ_state', ((e: CustomEvent) => {
    cachedGameData = e.detail;
  }) as EventListener);
}

function requestGameData(): any {
  setupGameDataBridge();

  const script = document.createElement('script');
  script.textContent = `
    (function() {
      try {
        const gd = window.gameui && window.gameui.gamedatas;
        if (gd) {
          window.dispatchEvent(new CustomEvent('__bga_civ_state', {
            detail: JSON.parse(JSON.stringify(gd))
          }));
        }
      } catch(e) {}
    })();
  `;
  document.head.appendChild(script);
  script.remove();

  return cachedGameData;
}

// ---------------------------------------------------------------------------
// Helpers — try multiple BGA field names defensively
// ---------------------------------------------------------------------------

function tryFields(obj: any, ...names: string[]): any {
  for (const name of names) {
    if (obj && obj[name] !== undefined) return obj[name];
  }
  return undefined;
}

function toArray(val: any): any[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === 'object') return Object.values(val);
  return [];
}

// ---------------------------------------------------------------------------
// Player ID mapping — BGA uses large numeric IDs; we need sequential 1,2,3…
// ---------------------------------------------------------------------------

function buildPlayerIdMap(gamedatas: any): Map<string, number> {
  const map = new Map<string, number>();

  // BGA provides ordering via playerorder, player_table_order, or natural_order
  const ordering: any[] =
    toArray(tryFields(gamedatas, 'playerorder', 'player_table_order', 'natural_order'));

  if (ordering.length > 0) {
    ordering.forEach((id, idx) => {
      map.set(String(id), idx + 1);
    });
  } else if (gamedatas.players && typeof gamedatas.players === 'object') {
    // Fallback: sort by BGA player ID numerically
    const ids = Object.keys(gamedatas.players).sort(
      (a, b) => Number(a) - Number(b)
    );
    ids.forEach((id, idx) => {
      map.set(id, idx + 1);
    });
  }

  return map;
}

// ---------------------------------------------------------------------------
// Map / hex extraction
// ---------------------------------------------------------------------------

function extractMapState(gamedatas: any): any[] {
  const raw = tryFields(gamedatas, 'board', 'hexes', 'map_hexes', 'tiles', 'map', 'hex_tiles');
  if (!raw) return [];

  return toArray(raw).map((hex: any) => ({
    q: Number(hex.q ?? hex.x ?? hex.col ?? 0),
    r: Number(hex.r ?? hex.y ?? hex.row ?? 0),
    terrain: String(hex.terrain ?? hex.type ?? hex.terrain_type ?? 'unknown'),
    resource: hex.resource ?? hex.resource_type ?? null,
    natural_wonder: hex.natural_wonder ?? hex.wonder ?? null,
    barbarian: Boolean(hex.barbarian ?? hex.has_barbarian ?? false),
    city_state: hex.city_state ?? hex.citystate ?? null,
    fort: Boolean(hex.fort ?? hex.has_fort ?? false),
    explored: hex.explored !== undefined ? Boolean(hex.explored) : true,
  }));
}

// ---------------------------------------------------------------------------
// Player state extraction
// ---------------------------------------------------------------------------

function extractFocusRow(playerData: any): any[] {
  const raw = tryFields(playerData, 'focus_row', 'focus_bar', 'card_row', 'focus_cards');
  if (!raw) return [];

  return toArray(raw).map((card: any) => ({
    type: String(card.type ?? card.card_type ?? 'unknown'),
    slot: Number(card.slot ?? card.position ?? card.row_position ?? 0),
    tech_level: Number(card.tech_level ?? card.level ?? 1),
    trade_tokens: Number(card.trade_tokens ?? card.tokens ?? 0),
    government: Boolean(card.government ?? card.is_government ?? false),
    government_arrows: Number(card.government_arrows ?? card.arrows ?? card.arrow_count ?? 0),
  }));
}

function extractCities(playerData: any): any[] {
  const raw = tryFields(playerData, 'cities', 'city_tokens');
  if (!raw) return [];

  return toArray(raw).map((city: any) => ({
    q: Number(city.q ?? city.x ?? city.col ?? 0),
    r: Number(city.r ?? city.y ?? city.row ?? 0),
    is_capital: Boolean(city.is_capital ?? city.capital ?? false),
    is_mature: Boolean(city.is_mature ?? city.mature ?? false),
    wonder: city.wonder ?? city.wonder_name ?? null,
    on_fort: Boolean(city.on_fort ?? false),
  }));
}

function extractControlTokens(playerData: any): any[] {
  const raw = tryFields(playerData, 'control_tokens', 'control', 'tokens');
  if (!raw) return [];

  return toArray(raw).map((tok: any) => ({
    q: Number(tok.q ?? tok.x ?? tok.col ?? 0),
    r: Number(tok.r ?? tok.y ?? tok.row ?? 0),
    reinforced: Boolean(tok.reinforced ?? tok.is_reinforced ?? false),
    district: tok.district ?? tok.district_type ?? null,
  }));
}

function extractPieces(playerData: any, ...fieldNames: string[]): Array<{ q: number; r: number } | null> {
  const raw = tryFields(playerData, ...fieldNames);
  if (!raw) return [];

  return toArray(raw).map((piece: any) => {
    if (!piece || (piece.q === undefined && piece.x === undefined && piece.col === undefined)) {
      return null;
    }
    return {
      q: Number(piece.q ?? piece.x ?? piece.col ?? 0),
      r: Number(piece.r ?? piece.y ?? piece.row ?? 0),
    };
  });
}

function extractPlayerStates(gamedatas: any, playerIdMap: Map<string, number>): any[] {
  if (!gamedatas.players || typeof gamedatas.players !== 'object') return [];

  const players: any[] = [];

  for (const [bgaId, pData] of Object.entries(gamedatas.players) as [string, any][]) {
    const seqId = playerIdMap.get(bgaId) ?? 0;

    players.push({
      id: seqId,
      leader: String(pData.leader ?? pData.leader_name ?? pData.civilization ?? 'unknown'),
      government: pData.government ?? pData.government_type ?? null,
      focus_row: extractFocusRow(pData),
      tech_level: Number(pData.tech_level ?? pData.technology_level ?? 1),
      cities: extractCities(pData),
      control_tokens: extractControlTokens(pData),
      armies: extractPieces(pData, 'armies', 'army_tokens'),
      caravans: extractPieces(pData, 'caravans', 'caravan_tokens'),
      resources: toArray(tryFields(pData, 'resources', 'resource_list')).map(String),
      natural_wonders: toArray(tryFields(pData, 'natural_wonders', 'wonders_discovered')).map(String),
      trade_tokens_total: Number(pData.trade_tokens_total ?? pData.trade_tokens ?? pData.tokens ?? 0),
      diplomacy_cards: toArray(tryFields(pData, 'diplomacy_cards', 'diplomacy')).map(String),
      wonders_built: toArray(tryFields(pData, 'wonders_built', 'wonders')).map(String),
      victory_progress: (typeof pData.victory_progress === 'object' && pData.victory_progress)
        ? pData.victory_progress
        : {},
    });
  }

  // Sort by sequential ID so player 1 comes first
  players.sort((a, b) => a.id - b.id);
  return players;
}

// ---------------------------------------------------------------------------
// Victory cards
// ---------------------------------------------------------------------------

function extractVictoryCards(gamedatas: any): any[] {
  const raw = tryFields(gamedatas, 'victory_cards', 'agendas', 'agenda_cards', 'victory_conditions');
  if (!raw) return [];

  return toArray(raw).map((card: any) => ({
    id: String(card.id ?? card.card_id ?? ''),
    agenda_a: String(card.agenda_a ?? card.condition_a ?? card.side_a ?? ''),
    agenda_b: String(card.agenda_b ?? card.condition_b ?? card.side_b ?? ''),
    is_fort_card: Boolean(card.is_fort_card ?? card.fort_card ?? false),
  }));
}

// ---------------------------------------------------------------------------
// Barbarians
// ---------------------------------------------------------------------------

function extractBarbarians(gamedatas: any): any[] {
  const raw = tryFields(gamedatas, 'barbarians', 'barb_tokens', 'barbarian_tokens');
  if (!raw) return [];

  return toArray(raw).map((barb: any) => ({
    q: Number(barb.q ?? barb.x ?? barb.col ?? 0),
    r: Number(barb.r ?? barb.y ?? barb.row ?? 0),
  }));
}

// ---------------------------------------------------------------------------
// Move / turn number
// ---------------------------------------------------------------------------

function extractMoveNumber(gamedatas: any): number {
  const val = tryFields(gamedatas, 'move_nbr', 'turn', 'turn_number', 'round', 'move_number');
  return val ? Number(val) : 1;
}

// ---------------------------------------------------------------------------
// Main parser
// ---------------------------------------------------------------------------

export function parseCivilizationState(): BoardState | null {
  try {
    const gamedatas = requestGameData();
    if (!gamedatas) return null;

    // Log structure once for debugging during live testing
    if (!hasLoggedStructure) {
      hasLoggedStructure = true;
      console.log('[BGA-CIV] gamedatas structure:', Object.keys(gamedatas));
      if (gamedatas.players) {
        const sampleId = Object.keys(gamedatas.players)[0];
        if (sampleId) {
          console.log('[BGA-CIV] sample player keys:', Object.keys(gamedatas.players[sampleId]));
        }
      }
      if (gamedatas.gamestate) {
        console.log('[BGA-CIV] gamestate keys:', Object.keys(gamedatas.gamestate));
      }
    }

    const playerIdMap = buildPlayerIdMap(gamedatas);
    const playerCount = playerIdMap.size || 1;

    // Determine active player
    const activeBgaId = String(
      gamedatas.gamestate?.active_player
      ?? gamedatas.active_player
      ?? gamedatas.current_player_id
      ?? ''
    );
    const playerToMove = playerIdMap.get(activeBgaId) ?? 1;

    const moveNumber = extractMoveNumber(gamedatas);

    const gameData: Record<string, any> = {
      map: extractMapState(gamedatas),
      players: extractPlayerStates(gamedatas, playerIdMap),
      victory_cards: extractVictoryCards(gamedatas),
      event_dial: Number(tryFields(gamedatas, 'event_dial', 'event_track', 'event_counter') ?? 0),
      turn_number: moveNumber,
      barbarians: extractBarbarians(gamedatas),
    };

    // BoardState uses board/rows/cols for grid games; Civ uses hex map via game_data
    // Provide a minimal 1x1 board since the real state is in game_data
    return {
      game: 'civilizationanewdawn',
      board: [[0]],
      rows: 1,
      cols: 1,
      move_number: moveNumber,
      player_to_move: playerToMove,
      player_count: playerCount,
      game_data: gameData,
      source: 'bga',
    };
  } catch (err) {
    console.error('[BGA-CIV] Failed to parse state:', err);
    return null;
  }
}
