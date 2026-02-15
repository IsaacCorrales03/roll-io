from sqlalchemy import UUID
from .Event import Event
from .EventContext import EventContext

def LongRestEvent(actor_id):
    return Event(
        type="long_rest",
        context=EventContext(actor_id=actor_id),
        cancelable=False
    )

def MoveTokenEvent(token_id: UUID, x: int, y: int):
    return Event(
        type="token_moved",
        payload={"token_id": token_id, "x": x, "y": y},
        cancelable=False
    )
