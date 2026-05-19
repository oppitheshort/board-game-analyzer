import type { MomentumData } from '../shared/types';

export function createMomentumMeter(container: HTMLElement) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title">Advantage</div>
      <div class="win-prob-container">
        <div class="win-prob-labels">
          <div>
            <div class="win-prob-pct p1" id="p1-win-pct">50%</div>
            <div class="win-prob-name">Red</div>
          </div>
          <div style="text-align:right">
            <div class="win-prob-pct p2" id="p2-win-pct">50%</div>
            <div class="win-prob-name">Yellow</div>
          </div>
        </div>
        <div class="tug-bar-track">
          <div class="tug-bar-p1" id="tug-p1" style="width:50%"></div>
          <div class="tug-bar-p2" id="tug-p2" style="width:50%"></div>
          <div class="tug-bar-center"></div>
          <div class="tug-bar-divider" id="tug-divider" style="left:calc(50% - 2px)"></div>
        </div>
      </div>
      <div class="eval-summary" id="eval-summary">Waiting for game...</div>
    </div>
  `;

  const p1Pct = container.querySelector('#p1-win-pct') as HTMLElement;
  const p2Pct = container.querySelector('#p2-win-pct') as HTMLElement;
  const tugP1 = container.querySelector('#tug-p1') as HTMLElement;
  const tugP2 = container.querySelector('#tug-p2') as HTMLElement;
  const divider = container.querySelector('#tug-divider') as HTMLElement;
  const summary = container.querySelector('#eval-summary') as HTMLElement;

  function evalToWinPct(evalScore: number): number {
    return 1 / (1 + Math.exp(-evalScore * 4));
  }

  return {
    update(data: MomentumData, evalScore: number, evalLabel: string): void {
      const p1Win = evalToWinPct(evalScore);
      const p2Win = 1 - p1Win;

      const p1Percent = Math.round(p1Win * 100);
      const p2Percent = 100 - p1Percent;

      p1Pct.textContent = `${p1Percent}%`;
      p2Pct.textContent = `${p2Percent}%`;

      tugP1.style.width = `${p1Win * 100}%`;
      tugP2.style.width = `${p2Win * 100}%`;
      divider.style.left = `calc(${p1Win * 100}% - 2px)`;

      const trend = data.trend > 0.02 ? ' and rising' : data.trend < -0.02 ? ' and falling' : '';
      if (Math.abs(evalScore) < 0.05) {
        summary.innerHTML = `<span class="highlight even">Even position</span>${trend}`;
      } else if (evalScore > 0) {
        summary.innerHTML = `<span class="highlight p1">Red</span> ${evalLabel.replace(/Player \d\s*/i, '')}${trend}`;
      } else {
        summary.innerHTML = `<span class="highlight p2">Yellow</span> ${evalLabel.replace(/Player \d\s*/i, '')}${trend}`;
      }
    },
  };
}
