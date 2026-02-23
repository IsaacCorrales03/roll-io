from uuid import UUID
from typing import List

from src.core.game.Event import Event, EventContext, GameState
from src.core.game.Event import EventDispatcher  # si lo necesitas explícitamente
from src.core.game.Event import EventHandler

from .phase import Phase


class InitiativeService:
    """
    Servicio responsable de:
    - Validar fase de combate
    - Generar orden de iniciativa
    - Inicializar turno actual
    """

    def start_combat(self, state: GameState, participant_ids: List[UUID]) -> None:
        """
        Inicia el combate:
        - Cambia fase a COMBAT
        - Lanza tiradas de iniciativa
        - Establece orden
        - Define actor actual
        """

        if state.current_phase == Phase.COMBAT:
            raise RuntimeError("El combate ya está activo")

        state.current_phase = Phase.COMBAT

        state.dispatch(Event(
            type="combat_started",
            context=EventContext(),
            payload={
                "participants": [str(pid) for pid in participant_ids]
            },
            cancelable=False
        ))

        self._roll_and_order(state, participant_ids)

        self._initialize_first_turn(state)

    # =========================
    # CORE
    # =========================

    def _roll_and_order(self, state: GameState, participant_ids: List[UUID]) -> None:
        """
        Genera iniciativa usando el sistema existente de eventos.
        Se apoya en RollCommand + roll_result handlers.
        """

        initiatives = []

        for actor_id in participant_ids:

            # Emitimos evento para que el sistema existente maneje el roll
            roll_event = Event(
                type="initiative_roll_requested",
                context=EventContext(actor_id=actor_id),
                payload={
                    "dice": "1d20",
                    "reason": "initiative"
                },
                cancelable=False
            )

            state.dispatch(roll_event)

            # Buscar último roll_result asociado
            last_roll = self._get_last_roll_result(state, actor_id)

            if last_roll is None:
                raise RuntimeError(f"No se obtuvo resultado de iniciativa para {actor_id}")

            initiatives.append((actor_id, last_roll))

        # Orden descendente
        initiatives.sort(key=lambda x: x[1], reverse=True)

        state.initiative_order = [actor_id for actor_id, _ in initiatives]

        state.dispatch(Event(
            type="initiative_completed",
            context=EventContext(),
            payload={
                "order": [str(i) for i in state.initiative_order]
            },
            cancelable=False
        ))

    def _initialize_first_turn(self, state: GameState) -> None:
        if not state.initiative_order:
            raise RuntimeError("No hay participantes en iniciativa")

        state.current_turn = 1
        state.current_actor = state.initiative_order[0]

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

    # =========================
    # UTILIDAD
    # =========================

    def _get_last_roll_result(self, state: GameState, actor_id: UUID):
        """
        Busca el último evento roll_result del actor.
        Asume que los handlers existentes generan:
            type="roll_result"
            payload["value"]
        """

        for event in reversed(state.event_log):
            if (
                event.type == "roll_result"
                and event.context
                and event.context.actor_id == actor_id
            ):
                return event.payload.get("value")

        return None