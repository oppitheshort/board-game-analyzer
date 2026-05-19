import type { BoardState, Cell } from '../../shared/types';

let cachedGameData: any = null;
let listenerSetup = false;

function setupBridge(): void {
  if (listenerSetup) return;
  listenerSetup = true;
  window.addEventListener('__bga_c4_state', ((e: CustomEvent) => {
    cachedGameData = e.detail;
  }) as EventListener);
}

function requestGameData(): any {
  setupBridge();
  const script = document.createElement('script');
  script.textContent = `
    (function() {
      try {
        var gd = window.gameui && window.gameui.gamedatas;
        console.log('[BGA-Analyzer] gameui exists:', !!window.gameui);
        console.log('[BGA-Analyzer] gamedatas exists:', !!gd);
        if (gd) {
          console.log('[BGA-Analyzer] gamedatas keys:', Object.keys(gd).join(', '));
          console.log('[BGA-Analyzer] board field:', typeof gd.board, gd.board ? 'present' : 'absent');
          console.log('[BGA-Analyzer] tokens field:', typeof gd.tokens, gd.tokens ? 'present' : 'absent');
          window.dispatchEvent(new CustomEvent('__bga_c4_state', {
            detail: JSON.parse(JSON.stringify(gd))
          }));
        }
      } catch(e) {
        console.error('BGA C4 bridge error:', e);
      }
    })();
  `;
  document.head.appendChild(script);
  script.remove();
  return cachedGameData;
}

export function parseConnectFourBoard(): BoardState | null {
  const gd = requestGameData();

  if (gd) {
    console.log('[BGA-Analyzer] Got gamedatas, attempting parse...');
    const result = parseFromGameData(gd);
    if (result) {
      console.log('[BGA-Analyzer] Parsed board:', result.rows, 'x', result.cols, 'move', result.move_number);
      return result;
    }
    console.log('[BGA-Analyzer] parseFromGameData returned null, falling back to DOM');
  } else {
    console.log('[BGA-Analyzer] No gamedatas from bridge, falling back to DOM');
  }

  const domResult = parseFromDOM();
  console.log('[BGA-Analyzer] DOM parse result:', domResult ? 'success' : 'null');
  return domResult;
}

function parseFromGameData(gd: any): BoardState | null {
  const board = gd.board || gd.tokens || gd.pieces || gd.grid;
  if (!board) {
    console.log('[BGA-Analyzer] No board/tokens/pieces/grid field found in gamedatas');
    return null;
  }
  console.log('[BGA-Analyzer] Using board data, type:', typeof board, Array.isArray(board) ? 'array' : 'object');

  // BGA Connect Four board is typically an object keyed by "row_col" or a nested structure
  // Determine board dimensions from game options or the data itself
  let rows = 0;
  let cols = 0;

  // Try to get dimensions from game options
  const opts = gd.game_options || gd.gamestate?.options || {};
  // BGA board size option - try common patterns
  if (gd.board_rows) rows = Number(gd.board_rows);
  if (gd.board_cols) cols = Number(gd.board_cols);
  if (gd.rows) rows = Number(gd.rows);
  if (gd.cols) cols = Number(gd.cols);

  // If board is an object, parse it
  if (typeof board === 'object' && !Array.isArray(board)) {
    const grid: Record<string, number> = {};
    let maxRow = 0;
    let maxCol = 0;

    for (const key of Object.keys(board)) {
      const entry = board[key];
      let r: number, c: number, player: number;

      if (entry && typeof entry === 'object') {
        // Entry might be { row: N, col: N, player: N } or similar
        r = Number(entry.row ?? entry.y ?? entry.r ?? 0);
        c = Number(entry.col ?? entry.x ?? entry.c ?? entry.column ?? 0);
        player = Number(entry.player ?? entry.player_id ?? entry.color ?? 0);
      } else {
        // Key might be "row_col" format
        const parts = key.split('_');
        if (parts.length >= 2) {
          r = Number(parts[0]);
          c = Number(parts[1]);
          player = Number(entry);
        } else {
          continue;
        }
      }

      if (r > maxRow) maxRow = r;
      if (c > maxCol) maxCol = c;
      grid[`${r}_${c}`] = player;
    }

    if (!rows) rows = maxRow + 1;
    if (!cols) cols = maxCol + 1;

    if (rows < 4 || cols < 4) {
      rows = Math.max(rows, 6);
      cols = Math.max(cols, 7);
    }

    const result: Cell[][] = Array.from({ length: rows }, () => Array(cols).fill(0) as Cell[]);
    for (const [key, player] of Object.entries(grid)) {
      const [r, c] = key.split('_').map(Number);
      if (r < rows && c < cols && (player === 1 || player === 2)) {
        result[r][c] = player as Cell;
      }
    }

    const p1 = result.flat().filter(c => c === 1).length;
    const p2 = result.flat().filter(c => c === 2).length;
    const moveNum = p1 + p2;

    // Determine who moves next
    let playerToMove = 1;
    if (gd.gamestate?.active_player) {
      const activeId = String(gd.gamestate.active_player);
      const order = gd.playerorder || gd.player_table_order || [];
      const idx = order.indexOf(activeId) ?? order.indexOf(Number(activeId));
      playerToMove = idx >= 0 ? idx + 1 : (p1 <= p2 ? 1 : 2);
    } else {
      playerToMove = p1 <= p2 ? 1 : 2;
    }

    return {
      game: 'connect4',
      board: result,
      rows,
      cols,
      move_number: moveNum,
      player_to_move: playerToMove,
      source: 'bga',
    };
  }

  // Board is already an array
  if (Array.isArray(board)) {
    rows = board.length;
    cols = board[0]?.length || 7;
    const result: Cell[][] = board.map((row: any[]) =>
      row.map((cell: any) => {
        const v = Number(cell);
        return (v === 1 || v === 2 ? v : 0) as Cell;
      })
    );

    const p1 = result.flat().filter(c => c === 1).length;
    const p2 = result.flat().filter(c => c === 2).length;

    return {
      game: 'connect4',
      board: result,
      rows,
      cols,
      move_number: p1 + p2,
      player_to_move: p1 <= p2 ? 1 : 2,
      source: 'bga',
    };
  }

  return null;
}

// Fallback: parse from DOM visual elements
function parseFromDOM(): BoardState | null {
  const boardEl = document.querySelector(
    '#board, [id*="connectfour"], [id*="connect_four"], .board_container, [id*="board"], [class*="board"]'
  );
  if (!boardEl) return null;

  const pieces = boardEl.querySelectorAll(
    '[class*="piece"], [class*="token"], [class*="disc"], [id*="disc"], [id*="piece"], [class*="slot"]'
  );

  if (pieces.length === 0) return parseFromGrid(boardEl);
  return parseFromPieces(boardEl, pieces);
}

function parseFromPieces(boardEl: Element, pieces: NodeListOf<Element>): BoardState | null {
  const boardRect = boardEl.getBoundingClientRect();
  if (boardRect.width === 0 || boardRect.height === 0) return null;

  let maxCol = 6, maxRow = 5;
  const detected: Array<{ row: number; col: number; player: 1 | 2 }> = [];

  pieces.forEach((piece) => {
    const rect = piece.getBoundingClientRect();
    const cx = rect.left + rect.width / 2 - boardRect.left;
    const cy = rect.top + rect.height / 2 - boardRect.top;

    const classes = piece.className.toLowerCase();
    const id = piece.id.toLowerCase();
    const style = (piece as HTMLElement).style;

    let player: 1 | 2 | null = null;
    if (classes.includes('red') || classes.includes('player1') || classes.includes('player_1') || classes.includes('color_ff0000') || classes.includes('color_1')) player = 1;
    else if (classes.includes('yellow') || classes.includes('player2') || classes.includes('player_2') || classes.includes('color_ffff00') || classes.includes('color_2')) player = 2;
    else if (id.includes('red') || id.includes('player1')) player = 1;
    else if (id.includes('yellow') || id.includes('player2')) player = 2;
    else if (style.backgroundColor) {
      const bg = style.backgroundColor.toLowerCase();
      if (bg.includes('red') || bg.includes('rgb(255, 0') || bg.includes('rgb(255,0')) player = 1;
      else if (bg.includes('yellow') || bg.includes('rgb(255, 255') || bg.includes('rgb(255,255')) player = 2;
    }

    if (!player) return;

    const colGuess = Math.round((cx / boardRect.width) * (maxCol + 1) - 0.5);
    const rowGuess = Math.round((cy / boardRect.height) * (maxRow + 1) - 0.5);

    if (colGuess >= 0 && rowGuess >= 0) {
      if (colGuess > maxCol) maxCol = colGuess;
      if (rowGuess > maxRow) maxRow = rowGuess;
      detected.push({ row: rowGuess, col: colGuess, player });
    }
  });

  const rows = maxRow + 1;
  const cols = maxCol + 1;
  const board: Cell[][] = Array.from({ length: rows }, () => Array(cols).fill(0) as Cell[]);

  for (const d of detected) {
    if (d.row < rows && d.col < cols) {
      board[d.row][d.col] = d.player;
    }
  }

  const p1 = board.flat().filter(c => c === 1).length;
  const p2 = board.flat().filter(c => c === 2).length;

  return {
    game: 'connect4',
    board,
    rows,
    cols,
    move_number: p1 + p2,
    player_to_move: p1 <= p2 ? 1 : 2,
    source: 'bga',
  };
}

function parseFromGrid(boardEl: Element): BoardState | null {
  const cells = boardEl.querySelectorAll('td, [class*="cell"], [class*="square"]');
  if (cells.length < 42) return null;

  const cols = 7;
  const rows = Math.floor(cells.length / cols);
  const board: Cell[][] = Array.from({ length: rows }, () => Array(cols).fill(0) as Cell[]);

  cells.forEach((cell, i) => {
    const r = Math.floor(i / cols);
    const c = i % cols;
    if (r >= rows) return;

    const cl = cell.className.toLowerCase();
    if (cl.includes('red') || cl.includes('player1')) board[r][c] = 1;
    else if (cl.includes('yellow') || cl.includes('player2')) board[r][c] = 2;
  });

  const p1 = board.flat().filter(c => c === 1).length;
  const p2 = board.flat().filter(c => c === 2).length;

  return {
    game: 'connect4',
    board,
    rows,
    cols,
    move_number: p1 + p2,
    player_to_move: p1 <= p2 ? 1 : 2,
    source: 'bga',
  };
}
