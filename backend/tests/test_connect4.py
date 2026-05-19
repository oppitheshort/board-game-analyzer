import pytest
from app.engine.connect4.board import Board
from app.engine.connect4.evaluator import evaluate
from app.engine.connect4.solver import solve
from app.engine.connect4.game import Connect4Game


class TestBoard:
    def test_empty_board(self):
        b = Board.empty()
        assert b.rows == 6
        assert b.cols == 7
        assert b.moves_made == 0
        assert not b.is_draw()

    def test_legal_moves_empty(self):
        b = Board.empty()
        assert b.legal_moves() == [0, 1, 2, 3, 4, 5, 6]

    def test_play_increments_moves(self):
        b = Board.empty()
        b2 = b.play(3)
        assert b2.moves_made == 1
        b3 = b2.play(4)
        assert b3.moves_made == 2

    def test_can_play(self):
        b = Board.empty()
        assert b.can_play(0)
        for _ in range(6):
            b = b.play(0)
        assert not b.can_play(0)

    def test_vertical_win(self):
        b = Board.empty()
        for _ in range(3):
            b = b.play(0)  # P1
            b = b.play(1)  # P2
        b = b.play(0)  # P1 wins with 4 in col 0
        assert b.last_player_won()

    def test_horizontal_win(self):
        b = Board.empty()
        b = b.play(0).play(6).play(1).play(6).play(2).play(6).play(3)
        assert b.last_player_won()

    def test_diagonal_win(self):
        b = Board.empty()
        moves = [0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3]
        for col in moves:
            b = b.play(col)
        assert b.last_player_won()

    def test_no_win_yet(self):
        b = Board.empty().play(0).play(1)
        assert not b.last_player_won()
        assert not b.is_draw()

    def test_draw(self):
        b = Board.empty(rows=1, cols=2)
        b = b.play(0).play(1)
        assert b.is_draw()

    def test_from_grid(self):
        grid = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [1, 2, 0, 0, 0, 0, 0],
        ]
        b = Board.from_grid(grid, player_to_move=1)
        assert b.moves_made == 2
        out = b.to_grid()
        assert out[5][0] == 1
        assert out[5][1] == 2

    def test_to_grid_roundtrip(self):
        b = Board.empty()
        b = b.play(3).play(3).play(4).play(2)
        grid = b.to_grid()
        player_to_move = 1 if b.moves_made % 2 == 0 else 2
        b2 = Board.from_grid(grid, player_to_move=player_to_move)
        assert b2.to_grid() == grid

    def test_key_unique(self):
        b1 = Board.empty().play(0).play(1)
        b2 = Board.empty().play(1).play(0)
        assert b1.key() != b2.key()

    def test_variable_board_size(self):
        b = Board.empty(rows=8, cols=9)
        assert b.rows == 8
        assert b.cols == 9
        assert len(b.legal_moves()) == 9

    def test_full_column_removed_from_legal(self):
        b = Board.empty(rows=2, cols=3)
        b = b.play(0).play(0)
        legal = b.legal_moves()
        assert 0 not in legal
        assert 1 in legal
        assert 2 in legal


class TestEvaluator:
    def test_empty_board_eval(self):
        b = Board.empty()
        score = evaluate(b)
        assert isinstance(score, (int, float))

    def test_center_preference(self):
        b_center = Board.empty().play(3)
        b_edge = Board.empty().play(0)
        s_center = evaluate(b_center)
        s_edge = evaluate(b_edge)
        assert s_center != s_edge


class TestSolver:
    def test_finds_winning_move(self):
        b = Board.empty()
        b = b.play(0).play(6).play(1).play(6).play(2).play(5)
        result = solve(b, time_limit_ms=1000)
        assert result.best_move == 3
        assert result.score > 0

    def test_blocks_opponent_win(self):
        b = Board.empty()
        b = b.play(6).play(0).play(6).play(1).play(5).play(2)
        result = solve(b, time_limit_ms=1000)
        assert result.best_move == 3

    def test_solve_empty_board(self):
        b = Board.empty()
        result = solve(b, time_limit_ms=500)
        assert result.best_move in b.legal_moves()
        assert result.depth_reached >= 1

    def test_solve_returns_search_result(self):
        b = Board.empty().play(3)
        result = solve(b, time_limit_ms=500)
        assert result.best_move is not None
        assert result.nodes_searched > 0


class TestConnect4Game:
    def test_protocol_methods(self):
        game = Connect4Game.new()
        assert game.current_player() == 1
        moves = game.get_legal_moves()
        assert len(moves) == 7
        assert not game.is_terminal()

    def test_apply_move(self):
        game = Connect4Game.new()
        game2 = game.apply_move(3)
        assert game2.current_player() == 2
        assert game.current_player() == 1

    def test_from_grid(self):
        grid = [[0]*7 for _ in range(6)]
        grid[5][3] = 1
        game = Connect4Game.from_grid(grid, player_to_move=2)
        assert game.current_player() == 2

    def test_terminal_detection(self):
        game = Connect4Game.new()
        for col in [0, 6, 0, 6, 0, 6, 0]:
            game = game.apply_move(col)
        assert game.is_terminal()
        assert game.get_winner() == 1

    def test_evaluate_returns_number(self):
        game = Connect4Game.new()
        score = game.evaluate()
        assert isinstance(score, (int, float))

    def test_key(self):
        g1 = Connect4Game.new().apply_move(0)
        g2 = Connect4Game.new().apply_move(1)
        assert g1.key() != g2.key()
