import { login, register } from '../shared/api';
import type { BackgroundToPopup, ContentToBackground, PopupToBackground } from '../shared/messages';
import type { AnalysisResult, AuthState, BoardState, CaptureMode, ExtensionState } from '../shared/types';

const WS_BASE = 'ws://217.77.1.42/ws/analysis';

let ws: WebSocket | null = null;
let reconnectDelay = 1000;
let authState: AuthState = { token: null, email: null, isAuthenticated: false };
let extState: ExtensionState = { mode: 'bga', isWatching: false, isConnected: false };
let pendingBoardStates: BoardState[] = [];
let authLoaded: Promise<void>;

authLoaded = loadAuth();

async function loadAuth(): Promise<void> {
  const data = await chrome.storage.local.get(['token', 'email']);
  if (data.token) {
    authState = { token: data.token, email: data.email, isAuthenticated: true };
  }
}

async function saveAuth(token: string, email: string): Promise<void> {
  authState = { token, email, isAuthenticated: true };
  await chrome.storage.local.set({ token, email });
}

async function clearAuth(): Promise<void> {
  authState = { token: null, email: null, isAuthenticated: false };
  await chrome.storage.local.remove(['token', 'email']);
}

function connectWS(): Promise<void> {
  return new Promise((resolve) => {
    if (!authState.token) { resolve(); return; }
    if (ws?.readyState === WebSocket.OPEN) { resolve(); return; }
    if (ws?.readyState === WebSocket.CONNECTING) {
      ws.addEventListener('open', () => resolve(), { once: true });
      ws.addEventListener('error', () => resolve(), { once: true });
      return;
    }

    ws = new WebSocket(`${WS_BASE}?token=${authState.token}`);

    ws.onopen = () => {
      extState.isConnected = true;
      reconnectDelay = 1000;
      broadcastState();
      flushPending();
      resolve();
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as AnalysisResult;
      chrome.tabs.query({ url: ['*://boardgamearena.com/*', '*://en.boardgamearena.com/*'] }, (tabs) => {
        for (const tab of tabs) {
          if (tab.id) chrome.tabs.sendMessage(tab.id, { type: 'ANALYSIS_RESULT', payload: data }).catch(() => {});
        }
      });
    };

    ws.onclose = () => {
      extState.isConnected = false;
      ws = null;
      broadcastState();
      resolve();
      if (extState.isWatching && authState.isAuthenticated) {
        setTimeout(connectWS, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, 30000);
      }
    };

    ws.onerror = () => ws?.close();
  });
}

function disconnectWS(): void {
  ws?.close();
  ws = null;
  extState.isConnected = false;
}

function sendBoardState(state: BoardState): void {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'board_state', ...state }));
  } else {
    pendingBoardStates.push(state);
  }
}

function flushPending(): void {
  while (pendingBoardStates.length > 0 && ws?.readyState === WebSocket.OPEN) {
    const state = pendingBoardStates.shift()!;
    ws.send(JSON.stringify({ type: 'board_state', ...state }));
  }
}

function broadcastState(): void {
  const msg: BackgroundToPopup = { type: 'STATE_UPDATE', payload: { ...extState, ...authState } };
  chrome.runtime.sendMessage(msg).catch(() => {});
  chrome.tabs.query({ url: ['*://boardgamearena.com/*', '*://en.boardgamearena.com/*'] }, (tabs) => {
    for (const tab of tabs) {
      if (tab.id) chrome.tabs.sendMessage(tab.id, msg).catch(() => {});
    }
  });
}

chrome.runtime.onMessage.addListener((message: ContentToBackground | PopupToBackground, sender, sendResponse) => {
  (async () => {
    await authLoaded;

    switch (message.type) {
      case 'BOARD_STATE':
      case 'BOARD_STATE_DETECTED':
        sendBoardState(message.payload);
        break;

      case 'BGA_GAME_DETECTED':
        extState.isWatching = true;
        await connectWS();
        broadcastState();
        if (sender.tab?.id) {
          const tabId = sender.tab.id;
          chrome.tabs.sendMessage(tabId, { type: 'INJECT_SIDEBAR' }).catch(() => {});
          chrome.tabs.sendMessage(tabId, { type: 'START_EXTRACTION', gameType: message.payload.gameType }).catch(() => {});
        }
        break;

      case 'BGA_GAME_ENDED':
        extState.isWatching = false;
        disconnectWS();
        broadcastState();
        break;

      case 'LOGIN':
        try {
          const res = await login(message.payload.email, message.payload.password);
          await saveAuth(res.access_token, message.payload.email);
          sendResponse({ type: 'AUTH_SUCCESS', payload: { token: res.access_token, email: message.payload.email } });
        } catch (e: any) {
          sendResponse({ type: 'AUTH_ERROR', payload: { message: e.message } });
        }
        break;

      case 'REGISTER':
        try {
          const res = await register(message.payload.email, message.payload.password);
          await saveAuth(res.access_token, message.payload.email);
          sendResponse({ type: 'AUTH_SUCCESS', payload: { token: res.access_token, email: message.payload.email } });
        } catch (e: any) {
          sendResponse({ type: 'AUTH_ERROR', payload: { message: e.message } });
        }
        break;

      case 'SET_MODE':
        extState.mode = message.payload;
        broadcastState();
        break;

      case 'TOGGLE_WATCHING':
        extState.isWatching = !extState.isWatching;
        if (extState.isWatching) await connectWS();
        else disconnectWS();
        broadcastState();
        break;

      case 'LOGOUT':
        await clearAuth();
        disconnectWS();
        extState.isWatching = false;
        broadcastState();
        break;

      case 'GET_STATE':
        sendResponse({ type: 'STATE_UPDATE', payload: { ...extState, ...authState } });
        break;
    }
  })();
  return true;
});
