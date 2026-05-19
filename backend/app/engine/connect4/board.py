from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Board:
    mask: int
    current: int
    rows: int
    cols: int
    moves_made: int

    @staticmethod
    def empty(rows: int = 6, cols: int = 7) -> Board:
        return Board(mask=0, current=0, rows=rows, cols=cols, moves_made=0)

    @staticmethod
    def from_grid(grid: list[list[int]], player_to_move: int = 1) -> Board:
        rows = len(grid)
        cols = len(grid[0]) if grid else 0
        bpc = rows + 1
        mask = 0
        p1_bits = 0

        for c in range(cols):
            for r in range(rows):
                cell = grid[rows - 1 - r][c]
                if cell != 0:
                    bit = 1 << (c * bpc + r)
                    mask |= bit
                    if cell == 1:
                        p1_bits |= bit

        p2_bits = mask ^ p1_bits
        moves_made = bin(mask).count("1")
        p1_count = bin(p1_bits).count("1")
        p2_count = bin(p2_bits).count("1")

        if player_to_move == 1:
            current = p1_bits if p1_count == p2_count else p2_bits
        else:
            current = p2_bits if p1_count == p2_count else p1_bits

        return Board(mask=mask, current=current, rows=rows, cols=cols, moves_made=moves_made)

    @property
    def _bpc(self) -> int:
        return self.rows + 1

    def _col_mask(self, col: int) -> int:
        return ((1 << self._bpc) - 1) << (col * self._bpc)

    def can_play(self, col: int) -> bool:
        top_bit = 1 << (col * self._bpc + self.rows - 1)
        return (self.mask & top_bit) == 0

    def legal_moves(self) -> list[int]:
        return [c for c in range(self.cols) if self.can_play(c)]

    def play(self, col: int) -> Board:
        bit = (self.mask + (1 << (col * self._bpc))) & self._col_mask(col)
        new_mask = self.mask | bit
        return Board(
            mask=new_mask,
            current=self.mask ^ self.current,
            rows=self.rows,
            cols=self.cols,
            moves_made=self.moves_made + 1,
        )

    def has_won(self, player_bits: int) -> bool:
        bpc = self._bpc
        for d in [1, bpc, bpc - 1, bpc + 1]:
            m = player_bits & (player_bits >> d)
            if m & (m >> (2 * d)):
                return True
        return False

    def last_player_won(self) -> bool:
        return self.has_won(self.mask ^ self.current)

    def is_draw(self) -> bool:
        return self.moves_made == self.rows * self.cols and not self.last_player_won()

    def key(self) -> int:
        return self.mask + self.current

    def opponent_bits(self) -> int:
        return self.mask ^ self.current

    def to_grid(self) -> list[list[int]]:
        bpc = self._bpc
        opp = self.opponent_bits()
        is_p1_turn = (self.moves_made % 2) == 0
        grid = [[0] * self.cols for _ in range(self.rows)]
        for c in range(self.cols):
            for r in range(self.rows):
                bit = 1 << (c * bpc + r)
                if self.current & bit:
                    grid[self.rows - 1 - r][c] = 1 if is_p1_turn else 2
                elif opp & bit:
                    grid[self.rows - 1 - r][c] = 2 if is_p1_turn else 1
        return grid
