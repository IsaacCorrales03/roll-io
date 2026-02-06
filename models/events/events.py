from .Event import Event
from .EventContext import EventContext

def LongRestEvent(actor_id):
    return Event(
        type="long_rest",
        context=EventContext(actor_id=actor_id),
        cancelable=False
    )