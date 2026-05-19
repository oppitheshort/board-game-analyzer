from app.engine.connect4.board import Board


def evaluate(board: Board) -> int:
    current = board.current
    opponent = board.opponent_bits()
    score = 0

    score += _center_score(current, board) - _center_score(opponent, board)
    score += _threat_score(current, opponent, board) - _threat_score(opponent, current, board)

    return score


def _center_score(bits: int, board: Board) -> int:
    bpc = board._bpc
    center = board.cols // 2
    score = 0
    col_bits = bits >> (center * bpc)
    for r in range(board.rows):
        if col_bits & (1 << r):
            score += 3
    if board.cols % 2 == 0:
        col_bits = bits >> ((center - 1) * bpc)
        for r in range(board.rows):
            if col_bits & (1 << r):
                score += 2
    return score


def _threat_score(mine: int, theirs: int, board: Board) -> int:
    score = 0
    empty = board._col_mask(0)
    for c in range(board.cols):
        empty |= board._col_mask(c)
    empty = (~board.mask) & empty

    bpc = board._bpc
    for d in [1, bpc, bpc - 1, bpc + 1]:
        score += _count_threats(mine, theirs, empty, d)
    return score


def _count_threats(mine: int, theirs: int, empty: int, direction: int) -> int:
    score = 0

    three = mine & (mine >> direction) & (mine >> (2 * direction))
    ext_left = (three << direction) & empty & ~theirs
    ext_right = (three >> (3 * direction)) & empty & ~theirs
    score += (bin(ext_left).count("1") + bin(ext_right).count("1")) * 50

    two = mine & (mine >> direction)
    gap_mask = ~(mine | theirs)
    ext_l = (two << direction) & gap_mask
    ext_r = (two >> (2 * direction)) & gap_mask
    score += (bin(ext_l).count("1") + bin(ext_r).count("1")) * 10

    return score
