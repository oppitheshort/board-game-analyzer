import './bga-detector';
import { startExtraction } from './game-state-extractor';
import { injectSidebar, sendToSidebar } from './sidebar-injector';
import type { BoardState } from '../shared/types';

let extractionStarted = false;

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'INJECT_SIDEBAR') {
    injectSidebar();
  }
  if (msg.type === 'START_EXTRACTION' && msg.gameType && !extractionStarted) {
    extractionStarted = true;
    startExtraction(msg.gameType, (state: BoardState) => {
      chrome.runtime.sendMessage({
        type: 'BOARD_STATE',
        payload: state,
      }).catch(() => {});
    });
  }
  if (msg.type === 'ANALYSIS_RESULT') {
    const data = msg.payload || msg.data;
    if (data) sendToSidebar(data);
  }
  if (msg.type === 'STATE_UPDATE' && msg.payload) {
    sendConnectionStatus(msg.payload.isConnected ?? false);
  }
});

function sendConnectionStatus(connected: boolean): void {
  const sidebar = document.querySelector('#bga-analyzer-sidebar iframe') as HTMLIFrameElement | null;
  sidebar?.contentWindow?.postMessage({ source: 'bga-analyzer', type: 'connection_status', connected }, '*');
}
