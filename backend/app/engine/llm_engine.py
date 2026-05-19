import json
import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are an expert board game analyst. You analyze board positions and evaluate them.

You will receive a board state for a game. Your job is to:
1. Evaluate the position on a scale from -1000 to +1000 (positive = Player 1 advantage, negative = Player 2 advantage, 0 = equal)
2. Rate the quality of the last move as one of: "Good", "Inaccuracy", "Mistake", "Blunder"
3. Provide a brief position assessment label

You must respond with ONLY a JSON object in this exact format, no other text:
{
  "eval_score": <integer from -1000 to 1000>,
  "move_quality": "<Good|Inaccuracy|Mistake|Blunder>",
  "eval_label": "<brief position assessment>",
  "reasoning": "<1-2 sentence internal reasoning>"
}

Guidelines for evaluation:
- eval_score near 0: roughly equal position
- eval_score 50-150: slight advantage
- eval_score 150-400: moderate advantage
- eval_score 400+: strong/winning advantage
- Use the full range. A forced win should be 900+.

Guidelines for move quality:
- Good: maintains or improves position, plays a strong move
- Inaccuracy: slightly suboptimal, misses a better option
- Mistake: clearly worse move, loses significant advantage
- Blunder: game-changing error, hangs pieces or misses a win

Be precise. You are an expert at every board game."""


def _format_board(board: list[list[int]], game: str, rows: int, cols: int) -> str:
    symbols = {0: ".", 1: "X", 2: "O"}
    lines = []
    for row in board:
        lines.append(" ".join(symbols.get(cell, str(cell)) for cell in row))
    col_labels = " ".join(str(i) for i in range(cols))
    return f"{chr(10).join(lines)}\n{col_labels}"


def _build_user_prompt(
    game: str,
    board: list[list[int]],
    rows: int,
    cols: int,
    move_number: int,
    player_to_move: int,
    prev_board: list[list[int]] | None = None,
) -> str:
    board_str = _format_board(board, game, rows, cols)

    game_rules = _get_game_rules(game, rows, cols)

    prompt = f"""Game: {game}
Board size: {rows} rows x {cols} columns
Move number: {move_number}
Player to move next: Player {player_to_move}
(Player 1 = X, Player 2 = O, Empty = .)

{game_rules}

Current board state:
{board_str}
"""

    if prev_board is not None:
        prev_str = _format_board(prev_board, game, rows, cols)
        prompt += f"""
Previous board state (before last move):
{prev_str}
"""

    if move_number == 0:
        prompt += "\nThis is the starting position. Rate it as 'Good' for move quality."
    else:
        player_who_moved = 2 if player_to_move == 1 else 1
        prompt += f"\nPlayer {player_who_moved} just made the last move (move #{move_number}). Evaluate the resulting position and rate the quality of that move."

    return prompt


def _get_game_rules(game: str, rows: int, cols: int) -> str:
    rules = {
        "connectfour": f"""Rules - Connect Four:
- Two players alternate dropping pieces into a {rows}x{cols} grid
- Pieces fall to the lowest available row in a column
- First player to get 4 in a row (horizontal, vertical, or diagonal) wins
- If the board fills up with no winner, it's a draw
- Column numbers are 0-{cols - 1} (left to right)
- Row 0 is the top, row {rows - 1} is the bottom""",
    }
    if game in rules:
        return rules[game]
    return f"Game: {game} ({rows}x{cols} board). Analyze the position based on your knowledge of this game's rules."


@dataclass
class LLMAnalysisResult:
    eval_score: float
    move_quality: str
    eval_label: str
    reasoning: str


async def analyze_with_llm(
    game: str,
    board: list[list[int]],
    rows: int,
    cols: int,
    move_number: int,
    player_to_move: int,
    prev_board: list[list[int]] | None = None,
) -> LLMAnalysisResult:
    if not settings.anthropic_api_key:
        raise RuntimeError("Anthropic API key not configured (set BGA_ANTHROPIC_API_KEY)")

    user_prompt = _build_user_prompt(
        game, board, rows, cols, move_number, player_to_move, prev_board
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "max_tokens": 300,
                "system": ANALYSIS_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        )

    if response.status_code != 200:
        logger.error("Anthropic API error %d: %s", response.status_code, response.text)
        raise RuntimeError(f"LLM analysis failed: HTTP {response.status_code}")

    data = response.json()
    text = data["content"][0]["text"].strip()

    try:
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response: %s", text)
        return LLMAnalysisResult(
            eval_score=0.0,
            move_quality="Good",
            eval_label="Analysis unavailable",
            reasoning="Failed to parse LLM response",
        )

    eval_score = max(-1000, min(1000, float(parsed.get("eval_score", 0))))
    move_quality = parsed.get("move_quality", "Good")
    if move_quality not in ("Good", "Inaccuracy", "Mistake", "Blunder"):
        move_quality = "Good"

    return LLMAnalysisResult(
        eval_score=eval_score,
        move_quality=move_quality,
        eval_label=parsed.get("eval_label", "Unknown"),
        reasoning=parsed.get("reasoning", ""),
    )
