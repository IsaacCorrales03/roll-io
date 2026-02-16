from typing import TypeVar, Generic

from src.core.game.results import QueryResult
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.game.Event import GameState
class Query:
    """Marker base. No lógica aquí."""
    pass

Q = TypeVar("Q", bound="Query")
R = TypeVar("R", bound="QueryResult")

class QueryHandler(Generic[Q, R]):
    def handle(self, query: Q, state: "GameState") -> R:
        raise NotImplementedError