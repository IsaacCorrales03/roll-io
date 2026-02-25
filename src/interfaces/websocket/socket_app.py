"""
WebSocket Handlers
Handles all real-time socket communication events
"""

from uuid import UUID, uuid4
from flask import request
from flask_socketio import emit, join_room
from numpy import character

# Models and queries
from src.core.combat.phase import Phase
from src.core.game.Action import AttackAction, EndTurnAction, StartCombatAction
from src.core.game.commands import AttackCommand, EndTurnCommand, StartCombatCommand
from src.shared.utils.items_utils import serialize_item_instance, item_instances, ItemInstance
from src.core.character.character import Character
from src.shared.utils.game_state_builder import build_game_state
from src.core.game.Event import MoveTokenEvent, Event
from src.core.game.querys import GetArmorClass, GetEntities

# Services
from src.features.auth.application.auth_service import AuthService
from src.features.campaigns.infrastructure.mysql_campaign_repository import MySQLCampaignRepository
from src.features.characters.infrastructure.character_repository import CharacterRepository
from src.shared.utils.tokens_utils import serialize_token

def register_socket_handlers(
    socketio,
    campaigns_dict: dict,
    game_states_dict: dict,
    connected_clients_dict: dict,
    socket_campaigns_dict: dict,
    auth_service: AuthService,
    campaign_repo: MySQLCampaignRepository,
    character_repo: CharacterRepository
):  
    
    """
    Register all WebSocket event handlers
    
    Args:
        socketio: SocketIO instance
        campaigns_dict: Shared dictionary for campaign data
        game_states_dict: Shared dictionary for game states
        connected_clients_dict: Shared dictionary for connected clients
        socket_campaigns_dict: Shared dictionary mapping socket IDs to campaign codes
        auth_service: Authentication service
        campaign_repo: Campaign repository
        character_repo: Character repository
    """
    
    def get_game_state(campaign_code: str):
        """Helper to get or create game state"""
        from src.shared.utils.game_state_builder import build_game_state
        
        if campaign_code not in game_states_dict:
            game_states_dict[campaign_code] = build_game_state(
                campaign_code, 
                campaigns_dict, 
                character_repo
            )
        return game_states_dict[campaign_code]

    @socketio.on("connect")
    def handle_connect():
        sid = request.sid  # type: ignore

        connected_clients_dict[sid] = {
            'connected_at': None,
            'username': None
        }

        emit("connection_confirmed", {
            "message": "Conectado exitosamente al servidor",
            "sid": sid
        })

    @socketio.on("join_campaign")
    def handle_join_campaign(data):
        code = data.get("code")
        if code not in campaigns_dict:
            return

        sid = request.sid  # type: ignore

        session_id = request.cookies.get("session_id")
        if not session_id:
            return

        session = auth_service.session_repo.get(UUID(session_id))
        if not session or session.revoked:
            return

        user = auth_service.user_repo.get_by_id(session.user_id)
        if not user:
            return

        join_room(code)
        socket_campaigns_dict[request.sid] = code  # type: ignore
        user_id = str(user.id)
        campaign_id = campaigns_dict[code]["campaign_id"]

        # Determine if user is DM
        campaign = campaign_repo.get_by_id(campaign_id)
        is_dm = campaign and str(campaign["owner_id"]) == user_id

        players = campaigns_dict[code]["players"]

        players[user_id] = {
            "user_id": user_id,
            "username": user.username,
            "character_uuid": players.get(user_id, {}).get("character_uuid"),
            "character_name": players.get(user_id, {}).get("character_name"),
            "sid": sid,
            "is_dm": is_dm
        }

        emit(
            "player_joined",
            {"players": list(players.values())},
            to=code
        )

    @socketio.on("start_campaign")
    def start_game(data):
        code = data.get("code")
        campaign = campaigns_dict.get(code)

        if not campaign:
            return

        players = campaign["players"].values()

        not_ready = [
            p for p in players
            if not p["is_dm"] and not p.get("character_uuid")
        ]

        if not_ready:
            emit(
                "campaign_start_error",
                {"reason": "No todos los jugadores están listos"},
                to=request.sid  # type: ignore
            )
            return

        emit(
            "campaign_started",
            {"code": code},
            to=code
        )

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid  # type: ignore

        if sid in connected_clients_dict:
            del connected_clients_dict[sid]

    @socketio.on("select_character")
    def handle_select_character(data):
        code = data.get("code")
        character_uuid = data.get("character_uuid")
        sid = request.sid  # type: ignore

        if code not in campaigns_dict:
            return

        for player in campaigns_dict[code]["players"].values():
            if player["sid"] == sid:
                character = character_repo.get_by_id(character_uuid)
                if not character:
                    return

                player["character_uuid"] = character_uuid
                player["character_name"] = character["name"]
                break

        emit(
            "player_joined",
            {"players": list(campaigns_dict[code]["players"].values())},
            to=code
        )

    @socketio.on("chat_message")
    def handle_chat_message(data):
        code = data.get("code")
        text = data.get("text", "").strip()
        sid = request.sid  # type: ignore

        if not text or code not in campaigns_dict:
            return

        sender = "Desconocido"

        for player in campaigns_dict[code]["players"].values():
            if player["sid"] == sid:
                sender = player["username"]
                break

        emit(
            "chat_message",
            {
                "sender": sender,
                "text": text
            },
            to=code
        )

    @socketio.on("get_ac")
    def handle_get_ac(data):
        try:
            actor_id = UUID(data["actor_id"])
        except Exception:
            emit("error", {"message": "Invalid actor_id"})
            return

        campaign_code = socket_campaigns_dict.get(request.sid)  # type: ignore
        if not campaign_code:
            emit("error", {"message": "Campaign not found"})
            return

        state = get_game_state(campaign_code)
        try:
            result = state.query(
                GetArmorClass(
                    actor_id=actor_id,
                    context="ui"
                )
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            emit("error", {"message": str(e)})
            return

        emit("ac_result", {
            "actor_id": str(actor_id),
            "value": result.value,
            "breakdown": result.breakdown
        })

    @socketio.on("move_token")
    def handle_move_token(data):
        campaign_code = data["campaign_code"]
        token_id = data["token_id"]
        x = data["x"]
        y = data["y"]
        state = game_states_dict[campaign_code]
        event = MoveTokenEvent(token_id=token_id, x=x, y=y)  # type: ignore
        try:
            state.dispatch(event)
            
            emit("token_moved", {
                "token_id": token_id,
                "x": x,
                "y": y
            }, to=campaign_code)
        except Exception as e:
            import traceback
            traceback.print_exc()
            emit("error", {"message": str(e)})

    @socketio.on("load_game_resources")
    def handle_load_game_resources(data):

        code = data.get("code")
        session_id = request.cookies.get("session_id")


        if not code or code not in campaigns_dict:
            emit("load_game_error", {"error": "Campaña no válida"})
            return

        if not session_id:
            emit("load_game_error", {"error": "No autenticado"})
            return

        session = auth_service.session_repo.get(UUID(session_id))
        if not session or session.revoked or not session.user_id:
            emit("load_game_error", {"error": "Sesión inválida"})
            return

        user_id = str(session.user_id)

        # -------------------------
        # CAMPAIGN
        # -------------------------
        campaign_model = campaigns_dict[code]
        campaign_instance = campaign_repo.get_by_id(campaign_model["campaign_id"])
        if not campaign_instance:
            emit("load_game_error", {"error": "Campaña no encontrada"})
            return

        # -------------------------
        # WORLD
        # -------------------------
        from flask import current_app
        services = current_app.extensions["services"]
        world = services["world_service"].get_by_id(campaign_instance["world_id"])
        if not world:
            emit("load_game_error", {"error": "Mundo no encontrado"})
            return

        # -------------------------
        # PLAYERS
        # -------------------------
        raw_players = campaign_model["players"]  
        players = []
        my_character_id = None
        is_dm = False

        for p in raw_players.values():
            player = {
                "user_id": p["user_id"],
                "username": p["username"],
                "character_uuid": p["character_uuid"],
                "is_dm": p["is_dm"]
            }
            players.append(player)

            if p["user_id"] == user_id:
                my_character_id = p["character_uuid"]
                is_dm = p["is_dm"]

        # -------------------------
        # GAME STATE
        # -------------------------
        if code not in game_states_dict:
            game_states_dict[code] = build_game_state(code, campaigns_dict, character_repo)
        game_state = game_states_dict[code]

        # -------------------------
        # TOKENS
        # -------------------------
        character_ids = [
            UUID(p["character_uuid"])
            for p in players
            if p.get("character_uuid")
        ]

        tokens = services["token_service"].get_by_characters(character_ids)

        my_token = None
        for token in tokens:
            game_state.add_token(token)
            if str(token["character_id"]) == my_character_id:
                my_token = token

        # -------------------------
        # SCENE
        # -------------------------
        current_scene = world.scenes[0] if world.scenes else None
        if not current_scene:
            emit("load_game_error", {"error": "Escena no encontrada"})
            return

        current_section = current_scene.sections[0] if current_scene.sections else None

        # -------------------------
        # EMIT DATA
        # -------------------------
        emit("game_resources_loaded", {
            "campaign": campaign_model,
            "players": players,
            "world": {
                "id": str(world.id),
                "name": world.name
            },
            "current_scene": {
                "id": str(current_scene.id),
                "name": current_scene.name,
                "map_url": current_scene.map_url
            },
            "current_section": current_section.to_dict() if current_section else None,
            "tokens": tokens,
            "my_character_id": my_character_id,
            "my_token": my_token,
            "is_dm": is_dm
        })


    @socketio.on("get_entities")
    def handle_get_entities(data): 
        campaign_code = socket_campaigns_dict.get(request.sid)  # type: ignore
        if not campaign_code:
            emit("error", {"message": "Campaign not found"})
            return

        state = get_game_state(campaign_code)

        try:
            result = state.query(GetEntities())
        except Exception as e:
            import traceback
            traceback.print_exc()
            emit("error", {"message": str(e)})
            return
        characters = [
            {
                "id": str(char.id),
                "name": char.name,
                "hp": char.hp,
                "max_hp": char.max_hp,
                "ac": char.calc_ac(),
                "texture": char.texture
                
            }
            for char in result.get("characters", [])
        ]

        enemies = [
            {
                "id": str(enemy.id),
                "name": enemy.name,
                "hp": enemy.hp,
                "max_hp": enemy.max_hp,
                "ac": enemy.ac,
                "texture": enemy.asset_url
            }
            for enemy in result.get("enemies", [])
        ]

        emit("entities_result", {
            "characters": characters,
            "enemies": enemies
        })

    @socketio.on("create_enemy")
    def handle_create_enemy(data):
        from uuid import uuid4

        token_id = str(uuid4())
        spawn_x, spawn_y = 0, 0

        required_fields = ["name", "hp", "max_hp", "ac", "asset", "size", "attributes", "attacks"]
        for field in required_fields:
            if field not in data:
                emit("error", {"message": f"Missing field: {field}"})
                return

        state = game_states_dict.get(data["campaign_code"])
        if not state:
            emit("error", {"message": "Invalid campaign"})
            return

        event = Event(
            type="create_enemy",
            payload={
                "id": token_id,
                "name": data["name"],
                "hp": data["hp"],
                "max_hp": data["max_hp"],
                "ac": data["ac"],
                "asset_url": data["asset"],
                "size": tuple(data["size"]),
                "attributes": data["attributes"],
                "attacks": data["attacks"],
                "position": (spawn_x, spawn_y)
            },
            cancelable=False
        )

        try:
            state.dispatch(event)
        except Exception as e:
            import traceback
            traceback.print_exc()
            emit("error", {"message": str(e)})
            return

        print(event.payload)
        # En create_enemy:
        socketio.emit("enemy_created", serialize_token(state.tokens[token_id]), to=data["campaign_code"])


    @socketio.on("get_tokens")
    def handle_get_tokens(data):
        state = game_states_dict[data["campaign_code"]]
        tokens = state.tokens.values()
        
        emit("tokens_sync", [serialize_token(t) for t in state.tokens.values()])

    @socketio.on("toggle_equip_item")
    def toggle_equip_item(data):

        character_id = data.get("character_id")
        item_id = data.get("item_id")
        if not character_id or not item_id:
            emit("error", {"message": "Invalid payload"})
            return

        campaign_code = socket_campaigns_dict.get(request.sid) #type: ignore
        if not campaign_code:
            emit("error", {"message": "Campaign not found"})
            return

        state = get_game_state(campaign_code)

        character: Character = state.characters.get(UUID(character_id))
        if not character:
            emit("error", {"message": "Character not found"})
            return

        target_instance = None

        for instance in character.inventory:
            if instance.item.item_id == item_id:
                target_instance = instance
                break
        if not target_instance:
            emit("error", {"message": "Item not found"})
            return
        # 🔥 Delegar al dominio
        if target_instance.equipped:
            character.unequip(target_instance)
        else:
            character.equip(target_instance)

        emit("item_equipped_toggled", {
            "character_id": character_id,
            "item_id": item_id,
            "equipped": target_instance.equipped
        }, to=campaign_code)

    @socketio.on("update_character_inventory")
    def update_character_inventory(data):
        character_id = data.get("character_id", None)
        if not character_id:
            emit("error", {"message":"Character not found"})
            return
        code = data.get("campaign_code")
        if not code:
            emit("error", {"message": "Campaign not found"})
            return
        state = get_game_state(code)
        character: Character = state.characters.get(UUID(character_id))
        character_data = character.to_json()
        inventory = character_data.get("inventory")
        weapon = character_data.get("weapon")
        armor = character_data.get("armor")
        shield = character_data.get("shield")
        emit("inventory_updated", {
            "inventory":inventory,
            "weapon": weapon,
            "armor": armor,
            "shield": shield
        })

    @socketio.on("get_character_data")
    def handle_get_character_data(data):
        character_id = data.get("character_id")
        if not character_id:
            emit("error", {"message": "Invalid payload"})
            return

        code = data.get("campaign_code")
        if not code or code not in campaigns_dict:
            emit("error", {"message": "Campaign not found"})
            return
        state = get_game_state(code)

        character = state.characters.get(UUID(character_id))
        if not character:
            emit("error", {"message": "Character not found"})
            return
        emit("character_data_received", character.to_json())

    @socketio.on("get_items")
    def handle_get_items():
        serialized = [serialize_item_instance(inst) for inst in item_instances]
        emit("items_result", serialized)



    @socketio.on("save_and_exit")
    def save_and_exit(data):
        campaign_code = data.get("campaign_code")
        if not campaign_code:
            emit("error", {"message": "Campaña no encontrada"})
            return

        state = get_game_state(campaign_code)  # <-- aquí obtienes el game_state con todos los characters

        from flask import current_app
        services = current_app.extensions["services"]
        character_service = services["character_service"]

        # Guardar todos los personajes
        for char in state.characters.values():  # char es instancia de Character
            character_service.save(char)

        # Limpiar estructuras de datos
        game_states_dict.pop(campaign_code, None)
        campaigns_dict.pop(campaign_code, None)

        # También eliminar cualquier socket asociado
        to_remove = [sid for sid, code in socket_campaigns_dict.items() if code == campaign_code]
        for sid in to_remove:
            socket_campaigns_dict.pop(sid, None)

        emit("campaign_closed", {"campaign_code": campaign_code}, to=campaign_code)

    from uuid import uuid4

    @socketio.on("dm_give_item")
    def dm_give_item(data):
        campaign_code = data.get("campaign_code")
        item_instance_id = data.get("item_instance_id")
        target_player_id = data.get("target_player_id")

        if not campaign_code:
            emit("error", {"message": "Campaña no encontrada"})
            return

        state = get_game_state(campaign_code)
        character: Character = state.characters.get(UUID(target_player_id))
        if not character:
            emit("error", {"message": "Jugador no encontrado"})
            return

        # Buscar el item base por su ID
        item_id = data.get("item_instance_id")  # renombrar a item_id para mayor claridad

#        Buscar el Item base por item_id
        base_item = next((i.item for i in item_instances if i.item.item_id == item_id), None)
        print("giving item")
        if not base_item:
            emit("error", {"message":"item no encontrado"})
            return
        # Crear nueva instancia de ItemInstance para el jugador
        new_instance = ItemInstance(base_item)
        # Opcional: asignar un ID único si ItemInstance no lo hace automáticamente
        new_instance.instance_id = str(uuid4())

        # Añadir al inventario
        success = character.add_item(new_instance)
        if not success:
            emit("error", {"message": "No se puede añadir el item al inventario"})
            return
        print(character.inventory)
        emit("dm_give_item_success", {"player_id": target_player_id})

    @socketio.on("start_combat")
    def start_combat(data):
        print(data)
        participants = data["combatants"]
        start_cmd = StartCombatCommand(
            participant_ids=participants
        )
        state = get_game_state(data["campaign_code"])
        StartCombatAction(start_cmd).execute(state)
        emit("combat_started")

    @socketio.on("enemy_attack")
    @socketio.on("player_attack")
    def handle_attack(data):
        state = get_game_state(data["campaig_code"])
        attack_command = AttackCommand(
            actor_id=data["character_id"],
            target_id=data["target_id"],
            mode=data["attack_mode"],
            advantage=data["advantage"],
            disadvantage=data["disadvantage"]
        )
        result = AttackAction(attack_command).execute(state)
        
        socketio.emit("attack_result", result.payload)

        next_turn(state, data["character_id"])

    def next_turn(game_state, actor_id):
        end_turn_cmd = EndTurnCommand(actor_id=actor_id)
        EndTurnAction(end_turn_cmd).execute(game_state)
        if game_state.current_phase != Phase.COMBAT:
            socketio.emit("combat_finished")
            return
        current_actor = game_state.current_actor
        socketio.emit("next_combatient", {"current_actor" : current_actor})
        return