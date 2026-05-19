import pytest
from app.ws.analysis_handler import (
    AnalysisSession,
    normalize_eval,
    eval_label,
    classify_move_quality,
)
from app.schemas.board import BoardStateMessage


class TestNormalizeEval:
    def test_zero(self):
        assert normalize_eval(0) == pytest.approx(0.0, abs=0.01)

    def test_positive(self):
        result = normalize_eval(500)
        assert 0 < result <= 1

    def test_negative(self):
        result = normalize_eval(-500)
        assert -1 <= result < 0

    def test_large_value_clamped(self):
        result = normalize_eval(100000)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_symmetry(self):
        pos = normalize_eval(300)
        neg = normalize_eval(-300)
        assert pos == pytest.approx(-neg, abs=0.01)


class TestEvalLabel:
    def test_equal(self):
        label = eval_label(0.02)
        assert "equal" in label.lower() or "Equal" in label

    def test_slight_advantage(self):
        label = eval_label(0.15)
        assert "slight" in label.lower()
        assert "1" in label

    def test_strong_advantage(self):
        label = eval_label(0.7)
        assert "strong" in label.lower()

    def test_player2_advantage(self):
        label = eval_label(-0.3)
        assert "2" in label


class TestMoveQuality:
    def test_good_move(self):
        assert classify_move_quality(0.01) == "Good"

    def test_inaccuracy(self):
        assert classify_move_quality(0.08) == "Inaccuracy"

    def test_mistake(self):
        assert classify_move_quality(0.2) == "Mistake"

    def test_blunder(self):
        assert classify_move_quality(0.5) == "Blunder"

    def test_zero_delta(self):
        assert classify_move_quality(0.0) == "Good"


class TestAnalysisSession:
    @pytest.mark.asyncio
    async def test_analyze_returns_no_best_move(self):
        session = AnalysisSession()
        msg = BoardStateMessage(
            type="board_state",
            game="connect4",
            board=[
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [1, 2, 0, 0, 0, 0, 0],
            ],
            rows=6,
            cols=7,
            move_number=2,
            player_to_move=1,
            source="bga",
        )
        result = await session.analyze(msg)
        result_dict = result.model_dump()
        assert "best_move" not in result_dict
        assert result.type == "analysis"
        assert -1 <= result.eval_score <= 1
        assert result.depth_reached >= 1
        assert result.move_quality in ("Good", "Inaccuracy", "Mistake", "Blunder")

    @pytest.mark.asyncio
    async def test_analyze_empty_board(self):
        session = AnalysisSession()
        msg = BoardStateMessage(
            type="board_state",
            game="connect4",
            board=[[0]*7 for _ in range(6)],
            rows=6,
            cols=7,
            move_number=0,
            player_to_move=1,
            source="screen_capture",
        )
        result = await session.analyze(msg)
        assert result.eval_label is not None
        assert len(result.momentum.history) >= 0

    @pytest.mark.asyncio
    async def test_momentum_builds_over_moves(self):
        session = AnalysisSession()
        boards = [
            [[0]*7 for _ in range(6)],
        ]
        # Play a few moves
        b1 = [[0]*7 for _ in range(6)]
        b1[5][3] = 1
        boards.append(b1)

        b2 = [row[:] for row in b1]
        b2[5][0] = 2
        boards.append(b2)

        for i, board in enumerate(boards):
            msg = BoardStateMessage(
                type="board_state",
                game="connect4",
                board=board,
                rows=6,
                cols=7,
                move_number=i,
                player_to_move=(i % 2) + 1,
                source="bga",
            )
            result = await session.analyze(msg)

        assert len(result.momentum.history) == 3

    @pytest.mark.asyncio
    async def test_player_strength_computed(self):
        session = AnalysisSession()
        msg = BoardStateMessage(
            type="board_state",
            game="connect4",
            board=[[0]*7 for _ in range(6)],
            rows=6,
            cols=7,
            move_number=0,
            player_to_move=1,
            source="bga",
        )
        result = await session.analyze(msg)
        assert 0 <= result.player_strength.p1 <= 100
        assert 0 <= result.player_strength.p2 <= 100
