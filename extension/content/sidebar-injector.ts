import type { AnalysisResult } from '../shared/types';

const SIDEBAR_WIDTH = 320;
const SIDEBAR_ID = 'bga-analyzer-sidebar';
const TOGGLE_ID = 'bga-analyzer-toggle';

let iframe: HTMLIFrameElement | null = null;
let container: HTMLDivElement | null = null;
let collapsed = false;

export function injectSidebar(): void {
  if (document.getElementById(SIDEBAR_ID)) return;

  container = document.createElement('div');
  container.id = SIDEBAR_ID;
  Object.assign(container.style, {
    position: 'fixed',
    top: '0',
    right: '0',
    width: `${SIDEBAR_WIDTH}px`,
    height: '100vh',
    zIndex: '999999',
    transition: 'transform 0.3s ease',
    boxShadow: '-2px 0 8px rgba(0,0,0,0.3)',
  });

  iframe = document.createElement('iframe');
  iframe.src = chrome.runtime.getURL('sidebar/index.html');
  Object.assign(iframe.style, {
    width: '100%',
    height: '100%',
    border: 'none',
  });
  container.appendChild(iframe);

  const toggle = document.createElement('button');
  toggle.id = TOGGLE_ID;
  toggle.textContent = '◀';
  Object.assign(toggle.style, {
    position: 'absolute',
    left: '-28px',
    top: '50%',
    transform: 'translateY(-50%)',
    width: '28px',
    height: '48px',
    border: 'none',
    borderRadius: '6px 0 0 6px',
    background: '#1a1a2e',
    color: '#e0e0e0',
    cursor: 'pointer',
    fontSize: '14px',
    zIndex: '1000000',
  });

  toggle.addEventListener('click', () => {
    collapsed = !collapsed;
    container!.style.transform = collapsed ? `translateX(${SIDEBAR_WIDTH}px)` : 'translateX(0)';
    toggle.textContent = collapsed ? '▶' : '◀';
  });

  container.appendChild(toggle);
  document.body.appendChild(container);
}

export function removeSidebar(): void {
  container?.remove();
  container = null;
  iframe = null;
}

export function sendToSidebar(data: AnalysisResult): void {
  iframe?.contentWindow?.postMessage({ source: 'bga-analyzer', data }, '*');
}
