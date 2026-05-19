import type { BoardState } from '../shared/types';

type Cell = 0 | 1 | 2;

export interface DetectionResult {
  board: Cell[][];
  rows: number;
  cols: number;
  confidence: number;
}

interface Rect { x: number; y: number; w: number; h: number; }

function rgbToHsl(r: number, g: number, b: number): [number, number, number] {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h = 0;
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / d + 2) / 6;
  else h = ((r - g) / d + 4) / 6;
  return [h * 360, s * 100, l * 100];
}

function findLargestBlueRegion(data: Uint8ClampedArray, width: number, height: number): Rect | null {
  let minX = width, minY = height, maxX = 0, maxY = 0;
  let blueCount = 0;

  for (let y = 0; y < height; y += 4) {
    for (let x = 0; x < width; x += 4) {
      const i = (y * width + x) * 4;
      const [h, s] = rgbToHsl(data[i], data[i + 1], data[i + 2]);
      if (h >= 200 && h <= 240 && s > 30) {
        blueCount++;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }

  if (blueCount < 50) return null;
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}

function classifyCell(data: Uint8ClampedArray, width: number, cx: number, cy: number, radius: number): Cell {
  let rSum = 0, ySum = 0, total = 0;
  const samples = 50;
  for (let i = 0; i < samples; i++) {
    const angle = (i / samples) * Math.PI * 2;
    const r = radius * 0.4 * Math.sqrt(i / samples);
    const px = Math.round(cx + r * Math.cos(angle));
    const py = Math.round(cy + r * Math.sin(angle));
    const idx = (py * width + px) * 4;
    if (idx < 0 || idx >= data.length - 3) continue;

    const [h, s, l] = rgbToHsl(data[idx], data[idx + 1], data[idx + 2]);
    total++;
    if (s > 40) {
      if ((h <= 20 || h >= 340) && l >= 30 && l <= 70) rSum++;
      else if (h >= 40 && h <= 70 && l >= 40 && l <= 80) ySum++;
    }
  }

  if (total === 0) return 0;
  const rPct = rSum / total, yPct = ySum / total;
  if (rPct > 0.3) return 1;
  if (yPct > 0.3) return 2;
  return 0;
}

function validateGravity(board: Cell[][]): boolean {
  const rows = board.length, cols = board[0]?.length ?? 0;
  for (let c = 0; c < cols; c++) {
    let foundEmpty = false;
    for (let r = 0; r < rows; r++) {
      if (board[r][c] === 0) foundEmpty = true;
      else if (foundEmpty) return false;
    }
  }
  return true;
}

export function detectBoard(imageData: ImageData): DetectionResult | null {
  const { data, width, height } = imageData;
  const roi = findLargestBlueRegion(data, width, height);
  if (!roi || roi.w < 100 || roi.h < 80) return null;

  const gridConfigs = [
    { cols: 7, rows: 6 }, { cols: 9, rows: 8 }, { cols: 8, rows: 9 },
    { cols: 9, rows: 9 }, { cols: 10, rows: 10 },
  ];

  let bestResult: DetectionResult | null = null;
  let bestConf = 0;

  for (const gc of gridConfigs) {
    const cellW = roi.w / gc.cols, cellH = roi.h / gc.rows;
    if (cellW < 10 || cellH < 10) continue;

    const board: Cell[][] = [];
    let filled = 0;
    for (let r = 0; r < gc.rows; r++) {
      const row: Cell[] = [];
      for (let c = 0; c < gc.cols; c++) {
        const cx = roi.x + (c + 0.5) * cellW;
        const cy = roi.y + (r + 0.5) * cellH;
        const cell = classifyCell(data, width, cx, cy, Math.min(cellW, cellH) / 2);
        row.push(cell);
        if (cell !== 0) filled++;
      }
      board.push(row);
    }

    if (filled === 0) continue;
    const gravityOk = validateGravity(board);
    const p1 = board.flat().filter(c => c === 1).length;
    const p2 = board.flat().filter(c => c === 2).length;
    const countOk = Math.abs(p1 - p2) <= 1;
    const conf = (gravityOk ? 0.5 : 0) + (countOk ? 0.3 : 0) + Math.min(0.2, filled / (gc.rows * gc.cols));

    if (conf > bestConf) {
      bestConf = conf;
      bestResult = { board, rows: gc.rows, cols: gc.cols, confidence: conf };
    }
  }

  return bestResult;
}

export function createBoardWatcher(onBoardChange: (state: BoardState) => void) {
  let prevBoard: string = '';
  let moveNumber = 0;
  let playerToMove: 1 | 2 = 1;

  return {
    processFrame(imageData: ImageData): void {
      const result = detectBoard(imageData);
      if (!result || result.confidence < 0.5) return;

      const key = JSON.stringify(result.board);
      if (key === prevBoard) return;

      const prevPieces = prevBoard ? JSON.parse(prevBoard).flat().filter((c: number) => c !== 0).length : 0;
      const newPieces = result.board.flat().filter(c => c !== 0).length;

      if (prevBoard && newPieces !== prevPieces + 1) return;

      prevBoard = key;
      moveNumber++;
      onBoardChange({
        game: 'connect4',
        board: result.board,
        rows: result.rows,
        cols: result.cols,
        move_number: moveNumber,
        player_to_move: playerToMove,
        source: 'screen_capture',
      });
      playerToMove = playerToMove === 1 ? 2 : 1;
    },
  };
}
