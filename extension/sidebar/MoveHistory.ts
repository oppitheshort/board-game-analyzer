import type { MomentumPoint } from '../shared/types';

export function createMoveHistory(container: HTMLElement) {
  container.innerHTML = `
    <div class="card">
      <div class="move-list-toggle" id="move-toggle">
        <span class="card-title" style="margin-bottom:0">Move Log</span>
        <span class="arrow" id="move-arrow">▼</span>
      </div>
      <div class="move-list-body" id="move-list-body">
        <div id="move-list" style="padding-top:8px"></div>
      </div>
    </div>
  `;

  const toggle = container.querySelector('#move-toggle') as HTMLElement;
  const arrow = container.querySelector('#move-arrow') as HTMLElement;
  const body = container.querySelector('#move-list-body') as HTMLElement;
  const list = container.querySelector('#move-list') as HTMLElement;

  const moves: Array<{ point: MomentumPoint; quality: string }> = [];
  let isOpen = false;

  toggle.addEventListener('click', () => {
    isOpen = !isOpen;
    body.classList.toggle('open', isOpen);
    arrow.classList.toggle('open', isOpen);
  });

  function render(): void {
    const recent = moves.slice(-30).reverse();
    list.innerHTML = recent
      .map(({ point, quality }) => {
        const deltaClass = point.delta >= 0 ? 'delta-up' : 'delta-down';
        const arrow = point.delta >= 0 ? '↑' : '↓';
        const pClass = point.player_who_moved === 1 ? 'p1' : 'p2';
        const pLabel = point.player_who_moved === 1 ? 'R' : 'Y';
        const qualityLower = quality.toLowerCase();
        const badgeClass = qualityLower === 'good' ? 'badge-good' :
          qualityLower === 'inaccuracy' ? 'badge-inaccuracy' :
          qualityLower === 'mistake' ? 'badge-mistake' : 'badge-blunder';
        return `
          <div class="move-item">
            <span class="move-number">#${point.move_number}</span>
            <span class="move-player ${pClass}">${pLabel}</span>
            <span class="move-delta ${deltaClass}">${arrow} ${Math.abs(point.delta).toFixed(2)}</span>
            <span class="badge ${badgeClass}">${quality}</span>
          </div>
        `;
      })
      .join('');
  }

  return {
    addMove(point: MomentumPoint, quality: string): void {
      moves.push({ point, quality });
      render();
    },
    clear(): void {
      moves.length = 0;
      list.innerHTML = '';
    },
  };
}
