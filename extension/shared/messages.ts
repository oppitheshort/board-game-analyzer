import type { AnalysisResult, AuthState, BoardState, CaptureMode, ExtensionState } from './types';

export type ContentToBackground =
  | { type: 'BOARD_STATE_DETECTED'; payload: BoardState }
  | { type: 'BGA_GAME_DETECTED'; payload: { gameType: string; tableId: string } }
  | { type: 'BGA_GAME_ENDED' };

export type BackgroundToContent =
  | { type: 'ANALYSIS_RESULT'; payload: AnalysisResult }
  | { type: 'START_WATCHING' }
  | { type: 'STOP_WATCHING' };

export type PopupToBackground =
  | { type: 'LOGIN'; payload: { email: string; password: string } }
  | { type: 'REGISTER'; payload: { email: string; password: string } }
  | { type: 'SET_MODE'; payload: CaptureMode }
  | { type: 'TOGGLE_WATCHING' }
  | { type: 'LOGOUT' }
  | { type: 'GET_STATE' };

export type BackgroundToPopup =
  | { type: 'AUTH_SUCCESS'; payload: { token: string; email: string } }
  | { type: 'AUTH_ERROR'; payload: { message: string } }
  | { type: 'STATE_UPDATE'; payload: ExtensionState & AuthState };
