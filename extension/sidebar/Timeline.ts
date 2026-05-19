import type { MomentumPoint } from '../shared/types';

export interface TimelineEntry {
  point: MomentumPoint;
  quality: string;
}

export function createTimeline(container: HTMLElement) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title">Game Timeline</div>
      <div class="timeline-container">
        <canvas class="eval-graph-canvas" id="eval-graph" height="80"></canvas>
        <div class="timeline-slider-row">
          <input type="range" class="timeline-slider" id="timeline-slider" min="0" max="0" value="0">
          <span class="timeline-move-label" id="timeline-label">Move 0</span>
        </div>
        <div class="timeline-hover-info" id="timeline-info">&nbsp;</div>
      </div>
    </div>
  `;

  const canvas = container.querySelector('#eval-graph') as HTMLCanvasElement;
  const slider = container.querySelector('#timeline-slider') as HTMLInputElement;
  const label = container.querySelector('#timeline-label') as HTMLElement;
  const info = container.querySelector('#timeline-info') as HTMLElement;

  const entries: TimelineEntry[] = [];
  let selectedIdx = -1;
  let hoverIdx = -1;

  function resizeCanvas(): void {
    const rect = canvas.parentElement!.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = 80;
  }

  function drawGraph(): void {
    const ctx = canvas.getContext('2d')!;
    const w = canvas.width;
    const h = canvas.height;
    const midY = h / 2;

    ctx.clearRect(0, 0, w, h);

    // Background
    ctx.fillStyle = '#0d1520';
    ctx.beginPath();
    ctx.roundRect(0, 0, w, h, 4);
    ctx.fill();

    // Center line
    ctx.strokeStyle = '#2a3a4a';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(w, midY);
    ctx.stroke();
    ctx.setLineDash([]);

    if (entries.length < 2) {
      ctx.fillStyle = '#5a6a7a';
      ctx.font = '11px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Waiting for moves...', w / 2, midY + 4);
      return;
    }

    const n = entries.length;
    const xStep = w / Math.max(n - 1, 1);

    // Build path points: eval clamped to [-1, 1], mapped to canvas
    const points: Array<{ x: number; y: number; eval: number }> = entries.map((e, i) => {
      const ev = Math.max(-1, Math.min(1, e.point.eval_score));
      return {
        x: i * xStep,
        y: midY - ev * (midY - 4),
        eval: ev,
      };
    });

    // Fill area: P1 advantage (above center) in red, P2 (below) in yellow
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];

      // Red fill (above center = positive eval = P1 advantage)
      ctx.beginPath();
      ctx.moveTo(p0.x, midY);
      ctx.lineTo(p0.x, Math.min(p0.y, midY));
      ctx.lineTo(p1.x, Math.min(p1.y, midY));
      ctx.lineTo(p1.x, midY);
      ctx.closePath();
      ctx.fillStyle = '#ff6b6b30';
      ctx.fill();

      // Yellow fill (below center = negative eval = P2 advantage)
      ctx.beginPath();
      ctx.moveTo(p0.x, midY);
      ctx.lineTo(p0.x, Math.max(p0.y, midY));
      ctx.lineTo(p1.x, Math.max(p1.y, midY));
      ctx.lineTo(p1.x, midY);
      ctx.closePath();
      ctx.fillStyle = '#ffd93d30';
      ctx.fill();
    }

    // Draw eval line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.strokeStyle = '#c8d6e5';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Draw dots for blunders/mistakes
    entries.forEach((e, i) => {
      const q = e.quality.toLowerCase();
      let dotColor = '';
      if (q === 'blunder') dotColor = '#ff4757';
      else if (q === 'mistake') dotColor = '#ff9f43';

      if (dotColor) {
        ctx.beginPath();
        ctx.arc(points[i].x, points[i].y, 3, 0, Math.PI * 2);
        ctx.fillStyle = dotColor;
        ctx.fill();
      }
    });

    // Hover / selection indicator
    const showIdx = hoverIdx >= 0 ? hoverIdx : selectedIdx;
    if (showIdx >= 0 && showIdx < points.length) {
      const pt = points[showIdx];
      ctx.beginPath();
      ctx.moveTo(pt.x, 0);
      ctx.lineTo(pt.x, h);
      ctx.strokeStyle = '#ffffff44';
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#fff';
      ctx.fill();
      ctx.strokeStyle = pt.eval >= 0 ? '#ff6b6b' : '#ffd93d';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }

  function formatInfo(idx: number): string {
    if (idx < 0 || idx >= entries.length) return '&nbsp;';
    const e = entries[idx];
    const player = e.point.player_who_moved === 1 ? '<span style="color:#ff6b6b">Red</span>' : '<span style="color:#ffd93d">Yellow</span>';
    const sign = e.point.eval_score >= 0 ? '+' : '';
    return `Move ${e.point.move_number} by ${player} &middot; Eval: ${sign}${e.point.eval_score.toFixed(2)} &middot; ${e.quality}`;
  }

  slider.addEventListener('input', () => {
    selectedIdx = parseInt(slider.value);
    label.textContent = `Move ${entries[selectedIdx]?.point.move_number ?? 0}`;
    info.innerHTML = formatInfo(selectedIdx);
    drawGraph();
  });

  canvas.addEventListener('mousemove', (ev) => {
    if (entries.length < 2) return;
    const rect = canvas.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const xStep = canvas.width / Math.max(entries.length - 1, 1);
    hoverIdx = Math.round(x / xStep);
    hoverIdx = Math.max(0, Math.min(entries.length - 1, hoverIdx));
    info.innerHTML = formatInfo(hoverIdx);
    drawGraph();
  });

  canvas.addEventListener('mouseleave', () => {
    hoverIdx = -1;
    info.innerHTML = selectedIdx >= 0 ? formatInfo(selectedIdx) : '&nbsp;';
    drawGraph();
  });

  canvas.addEventListener('click', (ev) => {
    if (entries.length < 2) return;
    const rect = canvas.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const xStep = canvas.width / Math.max(entries.length - 1, 1);
    selectedIdx = Math.round(x / xStep);
    selectedIdx = Math.max(0, Math.min(entries.length - 1, selectedIdx));
    slider.value = String(selectedIdx);
    label.textContent = `Move ${entries[selectedIdx]?.point.move_number ?? 0}`;
    info.innerHTML = formatInfo(selectedIdx);
    drawGraph();
  });

  setTimeout(resizeCanvas, 50);

  return {
    addMove(point: MomentumPoint, quality: string): void {
      entries.push({ point, quality });
      slider.max = String(Math.max(0, entries.length - 1));
      slider.value = slider.max;
      selectedIdx = entries.length - 1;
      label.textContent = `Move ${point.move_number}`;
      info.innerHTML = formatInfo(selectedIdx);
      resizeCanvas();
      drawGraph();
    },
    clear(): void {
      entries.length = 0;
      selectedIdx = -1;
      hoverIdx = -1;
      slider.max = '0';
      slider.value = '0';
      label.textContent = 'Move 0';
      info.innerHTML = '&nbsp;';
      drawGraph();
    },
    getEntries(): TimelineEntry[] {
      return entries;
    },
  };
}
