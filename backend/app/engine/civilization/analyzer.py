"""Entry point for Civilization: A New Dawn position analysis."""

from app.engine.civilization.evaluator import evaluate_position
from app.engine.civilization.state import CivGameState
from app.engine.router import EngineResult


def analyze_civ_position(
    game_data: dict,
    move_number: int,
    player_to_move: int,
) -> EngineResult:
    state = CivGameState.from_game_data(game_data)
    scores = evaluate_position(state)

    active_score = scores.get(player_to_move, 0.0)
    opponent_scores = [s for pid, s in scores.items() if pid != player_to_move]
    best_opponent = max(opponent_scores) if opponent_scores else 0.0
    raw_score = active_score - best_opponent

    return EngineResult(
        raw_score=raw_score,
        depth_reached=1,
        move_quality=None,
        eval_label=None,
        engine_used="handcoded",
    )
