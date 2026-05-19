from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchResult:
    best_move: Any
    score: float
    depth_reached: int
    nodes_searched: int


class GameProtocol(ABC):
    @abstractmethod
    def get_legal_moves(self) -> list:
        ...

    @abstractmethod
    def apply_move(self, move: Any) -> "GameProtocol":
        ...

    @abstractmethod
    def is_terminal(self) -> bool:
        ...

    @abstractmethod
    def get_winner(self) -> int | None:
        ...

    @abstractmethod
    def evaluate(self) -> float:
        ...

    @abstractmethod
    def current_player(self) -> int:
        ...

    @abstractmethod
    def key(self) -> int:
        ...
