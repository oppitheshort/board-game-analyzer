export function createPositionEval(container: HTMLElement) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title">Last Move</div>
      <div class="last-move-row">
        <span id="move-quality-badge" class="badge badge-good">--</span>
        <span id="depth-display" class="depth-label">Depth: --</span>
      </div>
    </div>
  `;

  const badge = container.querySelector('#move-quality-badge') as HTMLElement;
  const depthEl = container.querySelector('#depth-display') as HTMLElement;

  const classMap: Record<string, string> = {
    'Good': 'badge-good',
    'Inaccuracy': 'badge-inaccuracy',
    'Mistake': 'badge-mistake',
    'Blunder': 'badge-blunder',
  };

  return {
    update(moveQuality: string, depth: number): void {
      badge.textContent = moveQuality;
      badge.className = `badge ${classMap[moveQuality] || 'badge-good'}`;
      depthEl.textContent = `Depth: ${depth}`;
    },
  };
}
