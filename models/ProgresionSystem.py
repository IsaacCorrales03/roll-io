# models/systems/ProgressionSystem.py
class ProgressionSystem:

    @staticmethod
    def apply(actor, state):
        if actor.dnd_class.name == "Barbaro":
            ProgressionSystem._barbarian(actor, state)

    @staticmethod
    def _barbarian(actor, state):
        lvl = actor.level

        if lvl < 3:
            rage_uses = 2
            rage_bonus = 2
        elif lvl < 6:
            rage_uses = 3
            rage_bonus = 2
        elif lvl < 9:
            rage_uses = 4
            rage_bonus = 2
        elif lvl < 12:
            rage_uses = 4
            rage_bonus = 3
        elif lvl < 16:
            rage_uses = 5
            rage_bonus = 3
        elif lvl < 17:
            rage_uses = 5
            rage_bonus = 4
        elif lvl < 20:
            rage_uses = 6
            rage_bonus = 4
        else:
            rage_uses = 999
            rage_bonus = 4

        state.resources.setdefault(actor.id, {})
        state.resources[actor.id]["rage_uses"] = rage_uses
        state.resources[actor.id]["rage_bonus"] = rage_bonus
