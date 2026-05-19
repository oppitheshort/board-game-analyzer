import type { BoardState } from '../shared/types';
import { parseConnectFourBoard } from './games/connect-four';
import { parseCivilizationState } from './games/civilization';

type GameParser = () => BoardState | null;

const parsers: Record<string, GameParser> = {
  connectfour: parseConnectFourBoard,
  civilizationanewdawn: parseCivilizationState,
};

let currentGame: string | null = null;
let lastBoardKey = '';
let moveNumber = 0;

export function startExtraction(gameType: string, onBoardChange: (state: BoardState) => void): void {
  currentGame = gameType;
  lastBoardKey = '';
  moveNumber = 0;

  const observer = new MutationObserver(() => {
    extractAndNotify(onBoardChange);
  });

  const gameArea = document.querySelector('#game_play_area, #game_area, .game_interface');
  if (gameArea) {
    observer.observe(gameArea, { childList: true, subtree: true, attributes: true });
  }

  extractAndNotify(onBoardChange);
}

function extractAndNotify(onBoardChange: (state: BoardState) => void): void {
  if (!currentGame) return;

  const parser = parsers[currentGame];
  if (!parser) return;

  const state = parser();
  if (!state) return;

  const key = state.game_data
    ? JSON.stringify(state.game_data)
    : JSON.stringify(state.board);
  if (key === lastBoardKey) return;

  lastBoardKey = key;
  moveNumber++;

  onBoardChange({ ...state, move_number: moveNumber });
}
