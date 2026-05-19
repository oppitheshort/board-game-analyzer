export type Cell = 0 | 1 | 2;

export interface BoardState {
  game: string;
  board: Cell[][];
  rows: number;
  cols: number;
  move_number: number;
  player_to_move: number;
  player_count?: number;
  game_data?: Record<string, any>;
  source: 'bga' | 'screen_capture';
}

export interface MomentumPoint {
  move_number: number;
  eval_score: number;
  delta: number;
  player_who_moved: number;
}

export interface MomentumData {
  current: number;
  trend: number;
  history: MomentumPoint[];
}

export interface PlayerStrength {
  p1: number;
  p2: number;
  players?: Record<string, number>;
}

export interface AnalysisResult {
  type: 'analysis';
  eval_score: number;
  eval_label: string;
  depth_reached: number;
  momentum: MomentumData;
  player_strength: PlayerStrength;
  move_quality: string;
}

export interface AuthState {
  token: string | null;
  email: string | null;
  isAuthenticated: boolean;
}

export type CaptureMode = 'bga' | 'screen_capture';

export interface ExtensionState {
  mode: CaptureMode;
  isWatching: boolean;
  isConnected: boolean;
}
