"""Routes analysis requests to the appropriate engine.

If a handcoded engine exists for the game, use it (faster, deeper search).
Otherwise, fall back to the LLM engine (works for any game).
"""

import asyncio
import logging
from dataclasses import dataclass

from app.config import settings
from app.schemas.board import BoardStateMessage

logger = logging.getLogger(__name__)

HANDCODED_GAMES = {"connectfour", "connect4", "civilizationanewdawn", "civilization"}


@dataclass
class EngineResult:
    raw_score: float
    depth_reached: int
    move_quality: str | None  # LLM provides this; handcoded engine doesn't
    eval_label: str | None  # LLM provides this; handcoded engine doesn't
    engine_used: str  # "handcoded" or "llm"


async def analyze_position(
    msg: BoardStateMessage,
    prev_board: list[list[int]] | None = None,
) -> EngineResult:
    if msg.game in HANDCODED_GAMES:
        return await _run_handcoded(msg)

    return await _run_llm(msg, prev_board)


async def _run_handcoded(msg: BoardStateMessage) -> EngineResult:
    if msg.game in ("connectfour", "connect4"):
        from app.engine.connect4.board import Board
        from app.engine.connect4.solver import solve

        board = Board.from_grid(msg.board, msg.player_to_move)
        result = await asyncio.to_thread(solve, board, 500)

        return EngineResult(
            raw_score=result.score,
            depth_reached=result.depth_reached,
            move_quality=None,
            eval_label=None,
            engine_used="handcoded",
        )

    if msg.game in ("civilizationanewdawn", "civilization"):
        from app.engine.civilization.analyzer import analyze_civ_position

        return await asyncio.to_thread(
            analyze_civ_position,
            msg.game_data or {},
            msg.move_number,
            msg.player_to_move,
        )

    return EngineResult(
        raw_score=0.0,
        depth_reached=0,
        move_quality=None,
        eval_label=None,
        engine_used="handcoded",
    )


async def _run_llm(
    msg: BoardStateMessage,
    prev_board: list[list[int]] | None = None,
) -> EngineResult:
    from app.engine.llm_engine import analyze_with_llm

    if not settings.anthropic_api_key:
        logger.warning("No Anthropic API key — falling back to neutral evaluation")
        return EngineResult(
            raw_score=0.0,
            depth_reached=0,
            move_quality="Good",
            eval_label="LLM not configured",
            engine_used="llm",
        )

    result = await analyze_with_llm(
        game=msg.game,
        board=msg.board,
        rows=msg.rows,
        cols=msg.cols,
        move_number=msg.move_number,
        player_to_move=msg.player_to_move,
        prev_board=prev_board,
    )

    return EngineResult(
        raw_score=result.eval_score,
        depth_reached=1,
        move_quality=result.move_quality,
        eval_label=result.eval_label,
        engine_used="llm",
    )
