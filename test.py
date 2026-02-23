from src.core.game.EventHandlers import *
from src.core.game.querys import *
from src.core.game.commands import *
from src.core.game.Action import *
from src.core.character.character import Character
from src.core.character.enemy import Enemy, EnemyAttack
from src.core.game.Event import GameState
from src.core.character.dndclass import *
from src.core.character.race import *
from src.core.items.items import ITEMS, LONG_SWORD
from src.core.items.item import ItemInstance
import uuid

state = GameState()
hero = Character(
    id = uuid.uuid4(),
    owner_id=uuid.uuid4(),
    name="Subaru",
    race=RACE_MAP["Human"],
    dnd_class=CLASS_MAP["Barbaro"]()
)
sword_instance = ItemInstance(item=ITEMS[LONG_SWORD])

hero.add_item(sword_instance)
hero.equip(sword_instance)

goblin = Enemy(
    id=uuid.uuid4(),
    name="Goblin",
    hp=12,
    max_hp=12,
    ac=10,
    asset_url="none",
    attacks=[
        EnemyAttack(name="Scimitar", dice_count=1, dice_size=6, damage_bonus=2, attack_bonus=4, damage_type="slashing"),
        EnemyAttack(name="Shortbow", dice_count=1, dice_size=6, damage_bonus=2, attack_bonus=4, damage_type="piercing"),
    ]
)
state.add_character(hero)
state.add_enemy(goblin)
state.dispatcher.register("combat_ended", CombatEndHandler())
state.dispatcher.register("turn_ended", TurnEndedHandler())
state.dispatcher.register("attack_hit", ApplyDamageHandler())
state.dispatcher.register("combat_started", CombatStartedHandler())
state.register_query_handler(GetArmorClass, GetArmorClassHandler())
state.register_query_handler(GetStatModifier, GetStatModifierHandler())
state.register_query_handler(GetEntities, GetEntitiesHandler())



def iniciar_combate(enemigos: list[Enemy], jugadores: list[Actor], estado_de_juego):
    # Añadimos a los participantes
    participantes = []
    for enemigo in enemigos:
        participantes.append(enemigo.id)
    for jugador in jugadores:
        participantes.append(jugador.id)
    
    # Iniciamos el combate
    start_cmd = StartCombatCommand(
        participant_ids=participantes
    )
    StartCombatAction(start_cmd).execute(state)

    # Imprimimos la información inicial
    print("Combate iniciado, orden de turnos: ")
    for combatiente_id in state.initiative_order:
        combatiente = state.get_actor(combatiente_id)
        if combatiente:
            print(f"- {combatiente.name} | {combatiente.hp}HP")
    
    # Creamos el bucle de ataques:
    while state.current_phase == Phase.COMBAT:
        # Primero, evaluamos que realmente hay un actor ejecutando su turno actualmente:
        if state.current_actor:
            current_actor = state.get_actor(state.current_actor)
        else:
            raise RuntimeError("No hay un actor actualmente para ejecutar un ataque")

        # Ahora evaluamos si es un enemigo o un jugador:
        if isinstance(current_actor, Enemy):
            tipo_actor = "enemy"
        elif isinstance(current_actor, Actor):
            tipo_actor = "jugador"
        else:
            raise RuntimeError("No es un tipo de combatiente válido")
        
        # Ahora, hacemos el comando para atacar:
        if tipo_actor == "enemy":
            target = jugadores[0]
            attack_command = AttackCommand(
                current_actor.id,
                target.id,
                mode="melee",
                advantage=False,
                disadvantage=False,
                attack_name="Scimitar"
            )
        else: 
            target = enemigos[0]
            attack_command = AttackCommand(
                current_actor.id,
                target.id,
                mode="melee",
                advantage=False,
                disadvantage=False
            )
        # Ahora ejecutamos el comando:
        resultado_del_ataque = AttackAction(attack_command).execute(state)
        info = resultado_del_ataque.payload
        fallo = resultado_del_ataque.type == "attack_miss"
        ataque_cancelado = resultado_del_ataque.type == "attack_failed"
        if ataque_cancelado:
            print(f"{current_actor.name} No pudo realizar su ataque, debido a: {info["reason"]}")
        elif fallo:
            print(f"{current_actor.name} intentó atacar a {target.name}, pero falló")
        else:
            print(f"{current_actor.name} atacó a {target.name} y le infligió {info["damage"]} puntos de daño")
            if info["critical"]:
                print("Fue crítico!")


        endTurn_command = EndTurnCommand(current_actor.id)
        EndTurnAction(endTurn_command).execute(state)
        finalizo_el_combate = state.initiative_order == []
        if finalizo_el_combate: 
            print("El combate ha terminado")
            print("El ganador del combate es:", current_actor.name)


iniciar_combate([goblin], [hero], state)
