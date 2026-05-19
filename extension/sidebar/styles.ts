export function injectStyles(): void {
  const style = document.createElement('style');
  style.textContent = `
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #0f1923;
      color: #e0e0e0;
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      font-size: 13px;
      overflow-y: auto;
      overflow-x: hidden;
      width: 300px;
    }

    .sidebar-header {
      padding: 10px 16px;
      background: #1a2332;
      border-bottom: 1px solid #2a3a4a;
      text-align: center;
    }
    .sidebar-header h1 {
      font-size: 14px;
      font-weight: 700;
      color: #c8d6e5;
      letter-spacing: 1px;
      text-transform: uppercase;
    }

    /* Connection status */
    .status {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 16px;
      font-size: 11px;
      color: #5a6a7a;
      background: #141e2a;
    }
    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
    }
    .status-dot.connected { background: #00d26a; box-shadow: 0 0 6px #00d26a88; }
    .status-dot.disconnected { background: #ff4757; }

    /* Cards */
    .card {
      margin: 6px 8px;
      padding: 12px;
      background: #1a2332;
      border-radius: 8px;
      border: 1px solid #2a3a4a;
    }
    .card-title {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #5a6a7a;
      margin-bottom: 10px;
      font-weight: 600;
    }

    /* Win probability bar */
    .win-prob-container { margin-bottom: 6px; }
    .win-prob-labels {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 4px;
    }
    .win-prob-pct {
      font-size: 22px;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      transition: all 0.4s ease;
    }
    .win-prob-pct.p1 { color: #ff6b6b; }
    .win-prob-pct.p2 { color: #ffd93d; }
    .win-prob-name {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #5a6a7a;
    }

    /* Tug of war bar */
    .tug-bar-track {
      position: relative;
      height: 28px;
      border-radius: 14px;
      overflow: hidden;
      background: #0d1520;
      border: 1px solid #2a3a4a;
    }
    .tug-bar-p1 {
      position: absolute;
      top: 0;
      left: 0;
      height: 100%;
      background: linear-gradient(90deg, #ff6b6b, #ee5a24);
      transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      border-radius: 14px 0 0 14px;
    }
    .tug-bar-p2 {
      position: absolute;
      top: 0;
      right: 0;
      height: 100%;
      background: linear-gradient(90deg, #f9ca24, #ffd93d);
      transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      border-radius: 0 14px 14px 0;
    }
    .tug-bar-center {
      position: absolute;
      top: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 2px;
      height: 100%;
      background: #5a6a7a44;
      z-index: 2;
    }
    .tug-bar-divider {
      position: absolute;
      top: 2px;
      width: 4px;
      height: 24px;
      background: #fff;
      border-radius: 2px;
      z-index: 3;
      transition: left 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 0 8px rgba(255,255,255,0.5);
    }

    .eval-summary {
      text-align: center;
      margin-top: 8px;
      font-size: 12px;
      color: #8a9aaa;
      font-weight: 500;
    }
    .eval-summary .highlight { font-weight: 700; }
    .eval-summary .highlight.p1 { color: #ff6b6b; }
    .eval-summary .highlight.p2 { color: #ffd93d; }
    .eval-summary .highlight.even { color: #8a9aaa; }

    /* Last move badge */
    .last-move-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.3px;
    }
    .badge-good { background: #00d26a22; color: #00d26a; border: 1px solid #00d26a44; }
    .badge-inaccuracy { background: #ffd93d22; color: #ffd93d; border: 1px solid #ffd93d44; }
    .badge-mistake { background: #ff9f4322; color: #ff9f43; border: 1px solid #ff9f4344; }
    .badge-blunder { background: #ff475722; color: #ff4757; border: 1px solid #ff475744; }
    .depth-label { color: #5a6a7a; font-size: 11px; }

    /* Player accuracy */
    .accuracy-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }
    .accuracy-row:last-child { margin-bottom: 0; }
    .accuracy-player-label {
      font-size: 11px;
      font-weight: 600;
      width: 20px;
      text-align: center;
    }
    .accuracy-player-label.p1 { color: #ff6b6b; }
    .accuracy-player-label.p2 { color: #ffd93d; }
    .accuracy-bar-track {
      flex: 1;
      height: 6px;
      background: #0d1520;
      border-radius: 3px;
      overflow: hidden;
    }
    .accuracy-bar-fill {
      height: 100%;
      border-radius: 3px;
      transition: width 0.5s ease;
    }
    .accuracy-bar-fill.p1 { background: linear-gradient(90deg, #ff6b6b, #ee5a24); }
    .accuracy-bar-fill.p2 { background: linear-gradient(90deg, #f9ca24, #ffd93d); }
    .accuracy-pct {
      font-size: 12px;
      font-weight: 700;
      width: 38px;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }
    .accuracy-pct.p1 { color: #ff6b6b; }
    .accuracy-pct.p2 { color: #ffd93d; }

    /* Timeline / eval graph */
    .timeline-container { position: relative; }
    .eval-graph-canvas {
      width: 100%;
      height: 80px;
      border-radius: 4px;
      cursor: crosshair;
    }
    .timeline-slider-row {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 6px;
    }
    .timeline-slider {
      flex: 1;
      -webkit-appearance: none;
      appearance: none;
      height: 4px;
      background: #2a3a4a;
      border-radius: 2px;
      outline: none;
    }
    .timeline-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 14px;
      height: 14px;
      background: #fff;
      border-radius: 50%;
      cursor: pointer;
      box-shadow: 0 0 4px rgba(0,0,0,0.4);
    }
    .timeline-move-label {
      font-size: 11px;
      color: #5a6a7a;
      font-variant-numeric: tabular-nums;
      min-width: 50px;
      text-align: right;
    }
    .timeline-hover-info {
      font-size: 11px;
      color: #8a9aaa;
      text-align: center;
      margin-top: 4px;
      min-height: 16px;
    }

    /* Move list (collapsible) */
    .move-list-toggle {
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      user-select: none;
    }
    .move-list-toggle .arrow {
      font-size: 10px;
      color: #5a6a7a;
      transition: transform 0.2s;
    }
    .move-list-toggle .arrow.open { transform: rotate(180deg); }
    .move-list-body {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s ease;
    }
    .move-list-body.open { max-height: 300px; overflow-y: auto; }
    .move-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 4px 0;
      border-bottom: 1px solid #1a2332;
      font-size: 12px;
    }
    .move-number { color: #5a6a7a; width: 30px; font-variant-numeric: tabular-nums; }
    .move-player { width: 24px; font-weight: 700; }
    .move-player.p1 { color: #ff6b6b; }
    .move-player.p2 { color: #ffd93d; }
    .move-delta { font-weight: 600; font-variant-numeric: tabular-nums; }
    .delta-up { color: #00d26a; }
    .delta-down { color: #ff4757; }
  `;
  document.head.appendChild(style);
}
