import time
from dataclasses import dataclass
from enum import IntEnum

from app.engine.connect4.board import Board
from app.engine.connect4.evaluator import evaluate
from app.engine.protocol import SearchResult

INF = 1_000_000


class TTFlag(IntEnum):
    EXACT = 0
    LOWER = 1
    UPPER = 2


@dataclass(slots=True)
class TTEntry:
    score: int
    depth: int
    flag: TTFlag
    best_move: int | None


def _move_order(board: Board, tt_move: int | None) -> list[int]:
    moves = board.legal_moves()
    center = board.cols // 2
    moves.sort(key=lambda c: abs(c - center))
    if tt_move is not None and tt_move in moves:
        moves.remove(tt_move)
        moves.insert(0, tt_move)
    return moves


def negamax(
    board: Board,
    depth: int,
    alpha: int,
    beta: int,
    tt: dict[int, TTEntry],
    deadline: float,
) -> tuple[int, int | None]:
    if time.monotonic() > deadline:
        raise TimeoutError

    if board.last_player_won():
        return -(INF - board.moves_made), None

    if board.is_draw():
        return 0, None

    if depth == 0:
        return evaluate(board), None

    key = board.key()
    tt_move = None
    entry = tt.get(key)
    if entry and entry.depth >= depth:
        if entry.flag == TTFlag.EXACT:
            return entry.score, entry.best_move
        if entry.flag == TTFlag.LOWER:
            alpha = max(alpha, entry.score)
        elif entry.flag == TTFlag.UPPER:
            beta = min(beta, entry.score)
        if alpha >= beta:
            return entry.score, entry.best_move
        tt_move = entry.best_move

    moves = _move_order(board, tt_move)
    best_score = -INF
    best_move = moves[0] if moves else None
    orig_alpha = alpha

    for move in moves:
        child = board.play(move)
        score, _ = negamax(child, depth - 1, -beta, -alpha, tt, deadline)
        score = -score

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)
        if alpha >= beta:
            break

    if best_score <= orig_alpha:
        flag = TTFlag.UPPER
    elif best_score >= beta:
        flag = TTFlag.LOWER
    else:
        flag = TTFlag.EXACT

    tt[key] = TTEntry(score=best_score, depth=depth, flag=flag, best_move=best_move)
    return best_score, best_move


def solve(board: Board, time_limit_ms: float = 500) -> SearchResult:
    deadline = time.monotonic() + time_limit_ms / 1000.0
    tt: dict[int, TTEntry] = {}
    best_result = SearchResult(best_move=None, score=0.0, depth_reached=0, nodes_searched=0)
    max_depth = board.rows * board.cols - board.moves_made

    for depth in range(1, max_depth + 1):
        try:
            score, move = negamax(board, depth, -INF, INF, tt, deadline)
            best_result = SearchResult(
                best_move=move,
                score=float(score),
                depth_reached=depth,
                nodes_searched=len(tt),
            )
            if abs(score) >= INF - 100:
                break
        except TimeoutError:
            break

    return best_result
