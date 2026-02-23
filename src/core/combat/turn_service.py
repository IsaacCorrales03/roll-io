from src.core.game.Event import Event, EventContext, GameState
from .phase import Phase


class TurnService:
    """
    Servicio responsable de:
    - Finalizar turno actual
    - Avanzar al siguiente actor según initiative_order
    - Gestionar avance de ronda
    """

    def end_turn(self, state: GameState) -> None:
        if state.current_phase != Phase.COMBAT:
            raise RuntimeError("No se puede finalizar turno fuera de combate")

        if not state.current_actor:
            raise RuntimeError("No hay actor activo")

        if not state.initiative_order:
            raise RuntimeError("No existe orden de iniciativa")

        previous_actor = state.current_actor
        current_turn = state.current_turn

        state.dispatch(Event(
            type="turn_ended",
            context=EventContext(
                actor_id=previous_actor,
                turn=current_turn,
                phase="combat"
            ),
            payload={},
            cancelable=False
        ))

        self._advance_turn(state)

    # =========================
    # CORE
    # =========================

    def _advance_turn(self, state: GameState) -> None:

        order = state.initiative_order
        current_index = order.index(state.current_actor) # type: ignore

        next_index = current_index + 1

        # Nueva ronda
        if next_index >= len(order):
            next_index = 0
            state.current_turn += 1

            state.dispatch(Event(
                type="round_started",
                context=EventContext(
                    turn=state.current_turn,
                    phase="combat"
                ),
                payload={},
                cancelable=False
            ))

        state.current_actor = order[next_index]

        state.dispatch(Event(
            type="turn_started",
            context=EventContext(
                actor_id=state.current_actor,
                turn=state.current_turn,
                phase="combat"
            ),
            payload={},
            cancelable=False
        ))