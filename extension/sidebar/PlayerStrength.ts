import type { PlayerStrength as PS } from '../shared/types';

export function createPlayerStrength(container: HTMLElement) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title">Accuracy</div>
      <div class="accuracy-row">
        <span class="accuracy-player-label p1">R</span>
        <div class="accuracy-bar-track">
          <div class="accuracy-bar-fill p1" id="p1-acc-bar" style="width:50%"></div>
        </div>
        <span class="accuracy-pct p1" id="p1-acc-pct">50%</span>
      </div>
      <div class="accuracy-row">
        <span class="accuracy-player-label p2">Y</span>
        <div class="accuracy-bar-track">
          <div class="accuracy-bar-fill p2" id="p2-acc-bar" style="width:50%"></div>
        </div>
        <span class="accuracy-pct p2" id="p2-acc-pct">50%</span>
      </div>
    </div>
  `;

  const p1Bar = container.querySelector('#p1-acc-bar') as HTMLElement;
  const p2Bar = container.querySelector('#p2-acc-bar') as HTMLElement;
  const p1Pct = container.querySelector('#p1-acc-pct') as HTMLElement;
  const p2Pct = container.querySelector('#p2-acc-pct') as HTMLElement;

  return {
    update(strength: PS): void {
      p1Bar.style.width = `${strength.p1}%`;
      p2Bar.style.width = `${strength.p2}%`;
      p1Pct.textContent = `${strength.p1.toFixed(0)}%`;
      p2Pct.textContent = `${strength.p2.toFixed(0)}%`;
    },
  };
}
