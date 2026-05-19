from pydantic import BaseModel


class BoardStateMessage(BaseModel):
    type: str = "board_state"
    game: str
    board: list[list[int]] = []
    rows: int = 0
    cols: int = 0
    move_number: int
    player_to_move: int
    player_count: int = 2
    game_data: dict | None = None
    source: str = "bga"
