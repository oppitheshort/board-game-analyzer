from pydantic import BaseModel


class MomentumPoint(BaseModel):
    move_number: int
    eval_score: float
    delta: float
    player_who_moved: int


class MomentumData(BaseModel):
    current: float
    trend: float
    history: list[MomentumPoint]


class PlayerStrength(BaseModel):
    p1: float = 50.0
    p2: float = 50.0
    players: dict[str, float] = {}


class AnalysisResponse(BaseModel):
    type: str = "analysis"
    eval_score: float
    eval_label: str
    depth_reached: int
    momentum: MomentumData
    player_strength: PlayerStrength
    move_quality: str
