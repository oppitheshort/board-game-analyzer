import type { ContentToBackground } from '../shared/messages';

interface GameDetector {
  urlPatterns: RegExp[];
  domSelectors: string[];
  titleKeywords: string[];
  gameType: string;
}

const GAME_DETECTORS: GameDetector[] = [
  {
    gameType: 'connectfour',
    urlPatterns: [/boardgamearena\.com\/\d+\/connectfour/i],
    domSelectors: ['[id*="connectfour"]'],
    titleKeywords: ['connect'],
  },
  {
    gameType: 'civilizationanewdawn',
    urlPatterns: [/boardgamearena\.com\/\d+\/civilizationanewdawn/i],
    domSelectors: ['[id*="civilizationanewdawn"]', '[id*="civilization"]'],
    titleKeywords: ['civilization'],
  },
];

const TABLE_URL_PATTERN = /boardgamearena\.com\/table\?table=(\d+)/i;

function detectGame(): { gameType: string; tableId: string } | null {
  const url = window.location.href;
  const tableMatch = url.match(TABLE_URL_PATTERN) || url.match(/table=(\d+)/);

  if (!tableMatch) return null;

  const pageText = document.title.toLowerCase();

  for (const detector of GAME_DETECTORS) {
    // Check URL patterns
    if (detector.urlPatterns.some((pattern) => pattern.test(url))) {
      return { gameType: detector.gameType, tableId: tableMatch[1] };
    }

    // Check DOM selectors
    const domMatch = detector.domSelectors.some((sel) => document.querySelector(sel));
    if (domMatch) {
      return { gameType: detector.gameType, tableId: tableMatch[1] };
    }

    // Check page title keywords
    if (detector.titleKeywords.some((kw) => pageText.includes(kw))) {
      return { gameType: detector.gameType, tableId: tableMatch[1] };
    }
  }

  // Check for generic game name element (preserves original Connect Four fallback)
  const gameEl = document.querySelector('#game_name, .gameinfo_name');
  if (gameEl) {
    const gameText = gameEl.textContent?.toLowerCase() ?? '';
    for (const detector of GAME_DETECTORS) {
      if (detector.titleKeywords.some((kw) => gameText.includes(kw))) {
        return { gameType: detector.gameType, tableId: tableMatch[1] };
      }
    }
  }

  // Fallback: if a board element exists, assume Connect Four (legacy behavior)
  const boardEl = document.querySelector('[id*="board"], [class*="board"]');
  if (boardEl) {
    return { gameType: 'connectfour', tableId: tableMatch[1] };
  }

  return null;
}

function notifyBackground(msg: ContentToBackground): void {
  chrome.runtime.sendMessage(msg).catch(() => {});
}

let detected = false;

function checkForGame(): void {
  const game = detectGame();
  if (game && !detected) {
    detected = true;
    notifyBackground({ type: 'BGA_GAME_DETECTED', payload: game });
  }
}

const observer = new MutationObserver(() => {
  if (!detected) checkForGame();
});

observer.observe(document.body, { childList: true, subtree: true });

window.addEventListener('beforeunload', () => {
  if (detected) {
    notifyBackground({ type: 'BGA_GAME_ENDED' });
  }
  observer.disconnect();
});

checkForGame();
