import type { CaptureMode } from '../shared/types';

export function createConnectionStatus(container: HTMLElement) {
  container.innerHTML = `
    <div class="status">
      <div class="status-dot disconnected" id="status-dot"></div>
      <span id="status-text">Disconnected</span>
      <span id="mode-badge" style="margin-left:auto;font-size:10px;padding:2px 6px;border-radius:3px;background:#1a2332;color:#5a6a7a">--</span>
    </div>
  `;

  const dot = container.querySelector('#status-dot') as HTMLElement;
  const text = container.querySelector('#status-text') as HTMLElement;
  const modeBadge = container.querySelector('#mode-badge') as HTMLElement;

  return {
    setConnected(connected: boolean): void {
      dot.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
      text.textContent = connected ? 'Connected' : 'Disconnected';
    },
    setMode(mode: CaptureMode): void {
      const labels: Record<CaptureMode, string> = {
        bga: 'BGA',
        screen_capture: 'Screen Capture',
      };
      modeBadge.textContent = labels[mode] || '--';
    },
  };
}
