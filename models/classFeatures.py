from .base import ClassFeature, Actor
from typing import Optional
import random

class UnarmoredDefense(ClassFeature):
    name = "Unarmored Defense"
    description = "AC = 10 + DEX mod + CON mod si no llevas armadura."
    level = 1

    def apply(self, actor: Actor):
        actor.features.append(self)
        actor.ac_formulas.append(self.formula)

    def use(self, actor, turn_manager):
        return super().use(actor, turn_manager)
    
    def formula(self, actor: Actor) -> int:
        if actor.armor is None:
            return 10 + actor.dex_mod + actor.con_mod
        return 0

class Rage(ClassFeature):
    """Depende del turno: mantiene estado activo/inactivo durante varias rondas."""
    name = "Rage"
    description = "Furia que escala con nivel."
    level = 1
    def __init__(self):
        self.scaling = [
            (1, 2, 2),
            (3, 3, 2),
            (6, 4, 2),
            (9, 4, 3),
            (12, 5, 3),
            (16, 5, 4),
            (17, 6, 4),
            (20, float("inf"), 4)
        ]

        self.remaining_uses = 0
        self.in_rage = False
        self.bonus_damage = 0
        self.active = False  # Para turn manager

    def apply(self, actor: Actor):
        _, bonus_damage = self.get_current_bonus(actor.level)
        self.bonus_damage = bonus_damage
        actor.features.append(self)

    def use(self, actor, turn_manager) -> dict:
        """Activa o desactiva Rage según su estado."""
        if not self.in_rage and self.remaining_uses > 0:
            self.in_rage = True
            self.remaining_uses -= 1
            self.active = True
            return {
                "activado": True,
                "descripcion": f"{actor.name} entra en Rage, gana {self.get_current_bonus(actor.level)[1]} STR. Usos restantes: {self.remaining_uses}"
            }
        elif self.in_rage:
            self.in_rage = False
            self.active = False
            return {
                "activado": False,
                "descripcion": f"{actor.name} sale de Rage"
            }
        else:
            return {
                "activado": False,
                "descripcion": f"{actor.name} no puede usar Rage"
            }

    def get_current_bonus(self, level):
        for lvl, uses, bonus in reversed(self.scaling):
            if level >= lvl:
                self.remaining_uses = uses
                return uses, bonus
        return 0, 0

    def reset(self):
        """Se puede llamar al final del turno si queremos efectos temporales."""
        self.active = self.in_rage  # se mantiene activo solo si está en Rage

    def get_damage_bonus(self):
        return self.bonus_damage if self.in_rage else 0

    def get_resistances(self):
        return ["bludgeoning", "piercing", "slashing"] if self.in_rage else []

class RecklessAttack(ClassFeature):
    name = "Reckless Attack"
    description = (
            "Cuando atacas por primera vez en tu turno, puedes hacer un ataque temerario: "
            "ventaja en ataques cuerpo a cuerpo con Fuerza, pero los enemigos tienen ventaja hasta tu siguiente turno."
        )
    level = 2
    """Depende del turno: activo solo durante el turno del actor."""
    def __init__(self):
        self.active = False

    def apply(self, actor):
        actor.features.append(self)

    def use(self, actor, turn_manager):
        if turn_manager.round > 1:
            return {
                "activado": False,
                "descripcion": "Ataque temerario solo disponible en el primer turno de combate."
            }

        self.active = True
        return {
            "activado": True,
            "descripcion": f"{actor.name} activa ataque temerario este turno."
        }


    def reset(self):
        """Se llama al inicio de cada turno del actor para desactivar efectos temporales."""
        self.active = False

    def has_advantage(self) -> bool:
        return self.active

class BardicInspiration(ClassFeature):
    """Permite dar un dado de inspiración a otra criatura cercana, expira tras 10 turnos si no se usa."""
    DURATION_TURNS = 10  # duración máxima de un dado en turnos
    name = "Bardic Inspiration"
    description = "Puedes inspirar a los demás con palabras o música emotivas. Usa una acción adicional para dar un dado de inspiración a una criatura que pueda oírte. El dado puede sumarse a una tirada d20 una vez durante 10 minutos."
    level = 1
    def __init__(self):
        self.active = False
        self.die = 6
        self.remaining_uses = 0
        # Diccionario: target -> turnes restantes
        self.targets = {}

    def apply(self, actor: Actor):
        actor.features.append(self)
        self.remaining_uses = max(1, actor.cha_mod)

    def use(self, actor: Actor, turn_manager, **kwargs) -> dict:
        target: Optional[Actor] = kwargs.get("target")  # sigue siendo Optional[Actor]
        if not isinstance(target, Actor):
            target = None  # forzar tipo seguro
        if target is None:
            return {"activado": False, "descripcion": "No se especificó un objetivo."}

        if self.remaining_uses <= 0:
            return {
                "activado": False,
                "descripcion": f"{actor.name} no tiene usos de inspiración disponibles."
            }

        if target == actor:
            return {"activado": False, "descripcion": "No puedes darte inspiración a ti mismo."}

        if target in self.targets:
            return {"activado": False, "descripcion": f"{target.name} ya tiene un dado activo."}

        self.remaining_uses -= 1
        self.targets[target] = self.DURATION_TURNS
        self.active = True
        target.inspiration_dice[self] = {
            "die": self.die,                # cantidad de caras del dado
            "turns_left": self.DURATION_TURNS  # duración en turnos (10 minutos = 10 turnos)
        }

        return {
            "activado": True,
            "descripcion": f"{actor.name} inspira a {target.name} con un dado de {self.die}. Usos restantes: {self.remaining_uses}"
        }

    def roll_inspiration(self, target: Actor) -> int:
        """Se llama cuando la criatura decide usar el dado de inspiración."""
        if target not in self.targets:
            return 0
        roll = random.randint(1, self.die)
        del self.targets[target]  # El dado se pierde tras usarlo
        return roll

    def scale_die(self, level: int):
        """Escala el dado según el nivel del bardo."""
        if level >= 15:
            self.die = 12
        elif level >= 10:
            self.die = 10
        elif level >= 5:
            self.die = 8
        else:
            self.die = 6

    def tick(self):
        """Se llama al final de cada turno para decrementar duración de los dados activos."""
        expired = []
        for target, turns_left in self.targets.items():
            self.targets[target] -= 1
            if self.targets[target] <= 0:
                expired.append(target)
        for target in expired:
            del self.targets[target]

    def reset(self, actor: Actor):
        """Recupera los usos tras un descanso largo y limpia dados activos."""
        self.remaining_uses = max(1, actor.cha_mod)
        self.targets.clear()
        self.active = False

class SongOfRest(ClassFeature):
    name = "Song of Rest"
    description = "Otorga curación adicional durante un descanso corto."
    level = 2

    def __init__(self):
        self.die = 6

    def apply(self, actor: Actor):
        self.scale_die(actor.level)
        actor.features.append(self)

    def scale_die(self, level: int):
        if level >= 17:
            self.die = 12
        elif level >= 13:
            self.die = 10
        elif level >= 9:
            self.die = 8
        else:
            self.die = 6

    def use(self, actor: Actor, turn_manager, **kwargs) -> dict:
        """
        Solo usable durante un descanso corto.
        kwargs:
            targets: list[Actor] que gastaron dados de golpe
            context: "short_rest"
        """
        context = kwargs.get("context")
        targets = kwargs.get("targets", [])

        if context != "short_rest":
            return {
                "activado": False,
                "descripcion": "Canción de descanso solo puede usarse durante un descanso corto."
            }

        if not targets:
            return {
                "activado": False,
                "descripcion": "Nadie gastó dados de golpe."
            }

        results = {}
        for target in targets:
            bonus = random.randint(1, self.die)
            target.heal(bonus)
            results[target.name] = bonus

        return {
            "activado": True,
            "descripcion": f"{actor.name} usa Canción de descanso (1d{self.die})",
            "bonos": results
        }
    
