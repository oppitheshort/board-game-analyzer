from __future__ import annotations

from app.engine.connect4.board import Board
from app.engine.connect4.evaluator import evaluate
from app.engine.protocol import GameProtocol


class Connect4Game(GameProtocol):
    def __init__(self, board: Board) -> None:
        self._board = board

    @classmethod
    def from_grid(cls, grid: list[list[int]], player_to_move: int = 1) -> Connect4Game:
        return cls(Board.from_grid(grid, player_to_move))

    @classmethod
    def new(cls, rows: int = 6, cols: int = 7) -> Connect4Game:
        return cls(Board.empty(rows, cols))

    @property
    def board(self) -> Board:
        return self._board

    def get_legal_moves(self) -> list[int]:
        return self._board.legal_moves()

    def apply_move(self, move: int) -> Connect4Game:
        return Connect4Game(self._board.play(move))

    def is_terminal(self) -> bool:
        return self._board.last_player_won() or self._board.is_draw()

    def get_winner(self) -> int | None:
        if not self._board.last_player_won():
            return None
        return 2 if self.current_player() == 1 else 1

    def evaluate(self) -> float:
        return float(evaluate(self._board))

    def current_player(self) -> int:
        return 1 if self._board.moves_made % 2 == 0 else 2

    def key(self) -> int:
        return self._board.key()
