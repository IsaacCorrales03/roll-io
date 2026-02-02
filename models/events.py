# --- Sistema de eventos ---
class Event:
    """Representa un evento emitido por una feature o actor."""
    def __init__(self, name: str, source=None, payload=None):
        self.name = name        # nombre del evento, ej: 'on_turn_start'
        self.source = source    # quien lo emitió
        self.payload = payload  # datos extra

class EventListener:
    """Listener que registra callbacks y recibe eventos."""
    def __init__(self):
        self.subscribers = {}  # {evento_nombre: [callback1, callback2, ...]}

    def subscribe(self, event_name: str, callback):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    def emit(self, event: Event):
        """Llama a todos los callbacks registrados para el evento."""
        callbacks = self.subscribers.get(event.name, [])
        for cb in callbacks:
            cb(event)
