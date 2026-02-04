from uuid import uuid4

from models.character import Character
from models.events.Event import Event
from models.events.GameState import GameState
from models.events.EventContext import EventContext
from models.events.EventDispatcher import EventDispatcher
from models.events.EventHandler import EventHandler
from models.races import human
from models.dndclasses import Bard, Fighter
from models.commands import AttackCommand
from models.actions import AttackAction
from models.weapon import Weapon
from models.querys import *
sword = Weapon(
    name="Sword",
    dice_count=1,
    dice_size="1d8",
    attribute="STR",
    bonus=2,
    damage_type="slashing",
)
# ------------------------
# Handler de daño
# ------------------------
from models.events.EventHandlers import *

# ------------------------
# Simulación de ataque
# ------------------------
def main():
    # Crear personajes
    bard = Character(id=uuid4(), name="Himmel", race=human, dnd_class=Bard())
    fighter = Character(id=uuid4(), name="Thor", race=human, dnd_class=Fighter())
    bard.weapon = sword
    print(f"HP inicial de {fighter.name}: {fighter.hp}")

    # Crear dispatcher y GameState
    dispatcher = EventDispatcher()
    state = GameState(
        characters={bard.id: bard, fighter.id: fighter},
        current_turn=1,
        current_phase="combat",
        dispatcher=dispatcher
    )

    # Registrar handler de daño
    state.register_query_handler(GetArmorClass, GetArmorClassHandler())
    state.register_query_handler(GetStatModifier, GetStatModifierHandler())
    state.dispatcher.register("attack_hit", ApplyDamageHandler())
    bard.attributes["STR"] += 20
    # Bard ataca a Fighter
    attack_command = AttackCommand(
        actor_id=bard.id,
        target_id=fighter.id,
        mode="melee",
        adventage=False,
        disadventage=False
    )
    attack_action = AttackAction(attack_command)
    
    result_event = attack_action.execute(state)

    attacker_name = state.characters[attack_command.actor_id].name
    target_name = state.characters[attack_command.target_id].name
    print(result_event)

    if result_event.type == "attack_hit":
        print(f"{attacker_name} golpea a {target_name}!")
        print(f"  Daño aplicado: {result_event.payload['damage']}")
    else:
        print(f"{attacker_name} falla su ataque a {target_name}.")
        print(f"  Tirada de ataque: {result_event.payload['roll']} → total {result_event.payload['attack_score']} vs AC {result_event.payload['target_ac']}")

    print(f"HP final de {target_name}: {state.characters[attack_command.target_id].hp}")



if __name__ == "__main__":
    main()
