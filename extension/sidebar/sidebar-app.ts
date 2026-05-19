import { injectStyles } from './styles';
import { createMomentumMeter } from './MomentumMeter';
import { createPositionEval } from './PositionEval';
import { createTimeline } from './Timeline';
import { createMoveHistory } from './MoveHistory';
import { createPlayerStrength } from './PlayerStrength';
import { createConnectionStatus } from './ConnectionStatus';
import type { AnalysisResult } from '../shared/types';

injectStyles();

const app = document.getElementById('app')!;
app.innerHTML = `
  <div class="sidebar-header"><h1>Game Analyzer</h1></div>
  <div id="connection-status"></div>
  <div id="momentum-meter"></div>
  <div id="position-eval"></div>
  <div id="player-strength"></div>
  <div id="timeline"></div>
  <div id="move-history"></div>
`;

const connectionStatus = createConnectionStatus(document.getElementById('connection-status')!);
const momentumMeter = createMomentumMeter(document.getElementById('momentum-meter')!);
const positionEval = createPositionEval(document.getElementById('position-eval')!);
const playerStrength = createPlayerStrength(document.getElementById('player-strength')!);
const timeline = createTimeline(document.getElementById('timeline')!);
const moveHistory = createMoveHistory(document.getElementById('move-history')!);

window.addEventListener('message', (event) => {
  const msg = event.data;
  if (!msg) return;

  if (msg.source === 'bga-analyzer' && msg.data) {
    const result = msg.data as AnalysisResult;
    connectionStatus.setConnected(true);
    momentumMeter.update(result.momentum, result.eval_score, result.eval_label);
    positionEval.update(result.move_quality, result.depth_reached);
    playerStrength.update(result.player_strength);

    const latestPoint = result.momentum.history[result.momentum.history.length - 1];
    if (latestPoint) {
      timeline.addMove(latestPoint, result.move_quality);
      moveHistory.addMove(latestPoint, result.move_quality);
    }
  }

  if (msg.source === 'bga-analyzer' && msg.type === 'connection_status') {
    connectionStatus.setConnected(msg.connected);
  }

  if (msg.source === 'bga-analyzer' && msg.type === 'mode_change') {
    connectionStatus.setMode(msg.mode);
  }

  if (msg.source === 'bga-analyzer' && msg.type === 'game_reset') {
    timeline.clear();
    moveHistory.clear();
  }
});
