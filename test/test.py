from uuid import uuid4
from models.character import Character
from models.events.Event import Event
from models.events.GameState import GameState
from models.events.EventContext import EventContext
from models.events.EventDispatcher import EventDispatcher
from models.events.EventHandler import EventHandler
from models.races import human
from models.dndclasses import Bard, Barbarian
from models.commands import *
from models.actions.actions import *
from models.weapon import Weapon
from models.events.EventHandlers import *
from models.querys import *
from models.ProgresionSystem import ProgressionSystem

# Crear un arma simple
sword = Weapon(
    name="Sword",
    dice_count=1,
    dice_size="1d8",
    attribute="STR",
    bonus=2,
    damage_type="slashing",
)

def main():
    # Crear personajes
    bard = Character(id=uuid4(), name="Himmel", race=human, dnd_class=Bard())
    fighter = Character(id=uuid4(), name="Thor", race=human, dnd_class=Barbarian())  # solo ejemplo
    bard.weapon = sword
    fighter.weapon = sword
    print(f"Estados iniciales de {bard.name}: {getattr(bard, 'statuses', {})}")

    # Crear dispatcher y GameState
    dispatcher = EventDispatcher()
    state = GameState(
        characters={bard.id: bard, fighter.id: fighter},
        current_turn=1,
        current_phase="combat",
        dispatcher=dispatcher
    )

    # Registrar handler de aturdimiento
    dispatcher.register("attack_roll", StunnedAttackHandler())
    dispatcher.register("attack_hit", ApplyDamageHandler())
    dispatcher.register("status_requested", ApplyStatusHandler())
    dispatcher.register("attack_hit", RageDamageHandler())
    state.register_query_handler(GetArmorClass, GetArmorClassHandler())
    state.register_query_handler(GetStatModifier, GetStatModifierHandler())
    ProgressionSystem.apply(fighter, state)
    rage_action = UseRageAction(fighter.id)
    rage_event = rage_action.execute(state)
    

    # ------------------------
    # Aplicar estado "aturdido"
    # ------------------------
    status_command = StatusCommand(
        actor_id=bard.id,
        target_id=bard.id,
        status="aturdido",
        duration_turns=2
    )
    status_action = StatusAction(status_command)
    status_event = status_action.execute(state)    
    attack_command = AttackCommand(actor_id=bard.id, target_id=fighter.id, mode="melee", disadventage= False, adventage=False)
    attack_action = AttackAction(attack_command)

        # ------------------------
    # Turno del fighter
    # ------------------------
    attack_command_fighter = AttackCommand(
        actor_id=fighter.id,
        target_id=bard.id,
        mode="melee",
        disadventage=False,
        adventage=False
    )
    attack_action_fighter = AttackAction(attack_command_fighter)

    for i in range(2):
        try:
            print(fighter.status)
            attack_result = attack_action_fighter.execute(state)
            if attack_result.type == "attack_hit":
                print(f"{fighter.name} golpea a {bard.name}!")
                print(f"  Daño aplicado: {attack_result.payload['damage']}")
            else:
                print(f"{fighter.name} falla su ataque a {bard.name}.")
        except RuntimeError as e:
            print(f"{fighter.name} no puede atacar: {str(e)}")
        state.end_turn()

if __name__ == "__main__":
    main()
