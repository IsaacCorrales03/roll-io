from enum import Enum, auto


class Phase(Enum):
    """
    Fases globales del juego.
    Determinan qué reglas y validadores están activos.
    """

    EXPLORATION = auto()
    COMBAT = auto()
    REST = auto()
    DIALOGUE = auto()

    @classmethod
    def from_string(cls, value: str) -> "Phase":
        """
        Permite migrar desde el sistema antiguo basado en strings.
        """
        normalized = value.strip().upper()

        try:
            return cls[normalized]
        except KeyError:
            raise ValueError(f"Fase inválida: {value}")

    def __str__(self) -> str:
        return self.name.lower()


# =========================
# UTILIDADES
# =========================

def is_combat_phase(phase: Phase | None) -> bool:
    return phase == Phase.COMBAT


def require_phase(current: Phase | None, expected: Phase) -> None:
    """
    Validador simple para asegurar que una acción ocurre en la fase correcta.
    """
    if current != expected:
        raise RuntimeError(
            f"Operación inválida en fase {current}. Se requiere {expected}."
        )