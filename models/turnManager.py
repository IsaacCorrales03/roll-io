from .events import EventListener, Event
import random

# --- TurnManager integrado con eventos ---
class TurnManager:
    def __init__(self, combatants: list):
        self.combatants = combatants
        self.turn_order = []
        self.current_index = 0
        self.round = 1
        self.battle_active = True
        self.event_listener = EventListener()  # listener central

    def calculate_turn_order(self):
        for c in self.combatants:
            c.initiative_roll = c.attributes.get("DEX", 0) + random.randint(1, 20)
        self.turn_order = sorted(self.combatants, key=lambda c: c.initiative_roll, reverse=True)

    def start_combat(self):
        self.calculate_turn_order()
        self.current_index = 0
        self.round = 1
        self.battle_active = True
        print(f"Turn order round {self.round}: {[c.name for c in self.turn_order]}")

    def get_current_actor(self):
        return self.turn_order[self.current_index]

    def next_turn(self):
        actor = self.get_current_actor()
        # Emitir evento inicio de turno
        self.event_listener.emit(Event("on_turn_start", source=actor))
        self.current_index += 1
        if self.current_index >= len(self.turn_order):
            self.current_index = 0
            self.round += 1
            print(f"--- Ronda {self.round} ---")
        return self.get_current_actor()

    def end_turn(self):
        actor = self.get_current_actor()
        # Emitir evento fin de turno
        self.event_listener.emit(Event("on_turn_end", source=actor))
