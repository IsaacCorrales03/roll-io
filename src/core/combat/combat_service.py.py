from uuid import UUID
from typing import List

from src.core.game.Event import Event, EventContext, GameState

from .phase import Phase
from .initiative_service import InitiativeService
from .turn_service import TurnService


class CombatService:
    """
    Orquestador del dominio Combat.
    Controla inicio y finalización del combate.
    """

    def __init__(self):
        self._initiative_service = InitiativeService()
        self._turn_service = TurnService()

    # =========================
    # API PÚBLICA
    # =========================

    def start_combat(self, state: GameState, participant_ids: List[UUID]) -> None:
        self._initiative_service.start_combat(state, participant_ids)

    def end_turn(self, state: GameState) -> None:
        self._turn_service.end_turn(state)

    def end_combat(self, state: GameState) -> None:
        if state.current_phase != Phase.COMBAT:
            raise RuntimeError("No hay combate activo")

        state.dispatch(Event(
            type="combat_ended",
            context=EventContext(
                turn=state.current_turn,
                phase="combat"
            ),
            payload={},
            cancelable=False
        ))

        # Limpieza estructural
        state.current_phase = Phase.EXPLORATION
        state.current_actor = None
        state.current_turn = 0
        state.initiative_order = []