import math

from app.engine.router import analyze_position
from app.schemas.analysis import (
    AnalysisResponse,
    MomentumData,
    MomentumPoint,
    PlayerStrength,
)
from app.schemas.board import BoardStateMessage


def normalize_eval(raw_score: float) -> float:
    return 2.0 / (1.0 + math.exp(-raw_score / 300.0)) - 1.0


def eval_label(score: float) -> str:
    a = abs(score)
    side = "Player 1" if score > 0 else "Player 2"
    if a > 0.5:
        return f"{side} strong advantage"
    if a > 0.2:
        return f"{side} moderate advantage"
    if a > 0.05:
        return f"{side} slight advantage"
    return "Roughly equal"


def classify_move_quality(delta: float) -> str:
    d = abs(delta)
    if d < 0.05:
        return "Good"
    if d < 0.15:
        return "Inaccuracy"
    if d < 0.30:
        return "Mistake"
    return "Blunder"


def compute_momentum(history: list[MomentumPoint]) -> MomentumData:
    current = history[-1].eval_score if history else 0.0
    if len(history) < 2:
        return MomentumData(current=current, trend=0.0, history=history)
    recent = history[-3:]
    weights = [0.2, 0.3, 0.5][-len(recent):]
    trend = sum(w * p.delta for w, p in zip(weights, recent))
    return MomentumData(current=current, trend=trend, history=history)


def compute_player_strength(
    history: list[MomentumPoint], player_count: int = 2
) -> PlayerStrength:
    per_player: dict[int, tuple[int, int]] = {}  # player -> (good, total)
    for p in history:
        pid = p.player_who_moved
        good, total = per_player.get(pid, (0, 0))
        total += 1
        if abs(p.delta) < 0.15:
            good += 1
        per_player[pid] = (good, total)

    players_dict: dict[str, float] = {}
    for pid in range(1, player_count + 1):
        good, total = per_player.get(pid, (0, 0))
        players_dict[f"p{pid}"] = round((good / total) * 100, 1) if total else 50.0

    return PlayerStrength(
        p1=players_dict.get("p1", 50.0),
        p2=players_dict.get("p2", 50.0),
        players=players_dict,
    )


class AnalysisSession:
    def __init__(self) -> None:
        self.history: list[MomentumPoint] = []
        self._prev_eval: float = 0.0
        self._prev_board: list[list[int]] | None = None
        self.player_count: int = 2
        self._prev_player_to_move: int | None = None

    async def analyze(self, msg: BoardStateMessage) -> AnalysisResponse:
        # Set player_count from the first message received
        if not self.history:
            self.player_count = msg.player_count

        engine_result = await analyze_position(msg, self._prev_board)

        if engine_result.engine_used == "handcoded":
            norm_eval = normalize_eval(engine_result.raw_score)
            delta = norm_eval - self._prev_eval
            quality = classify_move_quality(delta) if msg.move_number > 0 else "Good"
            label = eval_label(norm_eval)
        else:
            norm_eval = normalize_eval(engine_result.raw_score)
            delta = norm_eval - self._prev_eval
            quality = engine_result.move_quality or classify_move_quality(delta)
            label = engine_result.eval_label or eval_label(norm_eval)

        # The player who just moved is the one who had the turn before this
        # message. For the first move, default to the last player in rotation.
        if self._prev_player_to_move is not None:
            player_who_moved = self._prev_player_to_move
        else:
            player_who_moved = self.player_count  # last in rotation

        self._prev_player_to_move = msg.player_to_move

        point = MomentumPoint(
            move_number=msg.move_number,
            eval_score=norm_eval,
            delta=delta,
            player_who_moved=player_who_moved,
        )
        self.history.append(point)
        self._prev_eval = norm_eval
        self._prev_board = [row[:] for row in msg.board]

        momentum = compute_momentum(self.history)
        strength = compute_player_strength(self.history, self.player_count)

        return AnalysisResponse(
            eval_score=round(norm_eval, 3),
            eval_label=label,
            depth_reached=engine_result.depth_reached,
            momentum=momentum,
            player_strength=strength,
            move_quality=quality,
        )
