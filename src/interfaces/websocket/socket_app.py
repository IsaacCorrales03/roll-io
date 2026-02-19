"""
WebSocket Handlers
Handles all real-time socket communication events
"""

from uuid import UUID, uuid4
from flask import request
from flask_socketio import emit, join_room

# Models and queries
from src.shared.utils.game_state_builder import build_game_state
from src.core.game.Event import MoveTokenEvent, Event
from src.core.game.querys import GetArmorClass, GetEntities

# Services
from src.features.auth.application.auth_service import AuthService
from src.features.campaigns.infrastructure.mysql_campaign_repository import MySQLCampaignRepository
from src.features.characters.infrastructure.character_repository import CharacterRepository
from src.shared.utils.tokens_utils import normalize_token

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
            print("Emitting token move:", token_id, x, y)
            
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
        from flask import current_app
        services = current_app.extensions["services"]

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
        print(result)
        print()
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
        token_id = str(uuid4())
        spawn_x = 0
        spawn_y = 0
        event = Event(
            type="create_enemy",
            payload={
                "id": token_id,
                "name": data["name"],
                "hp": data["hp"],
                "max_hp": data["max_hp"],
                "ac": data["ac"],
                "asset_url": data["asset"],
                "size": data["size"],
            },
            cancelable=False
        )
        state = game_states_dict[data["campaign_code"]]
        try:
            state.dispatch(event)
        except Exception as e:  
            import traceback
            traceback.print_exc()
            emit("error", {"message": str(e)})
            return
        
        socketio.emit("enemy_created", {
            "id": token_id,
            "name": data["name"],
            "hp": data["hp"],
            "max_hp": data["max_hp"],
            "asset": data["asset"],
            "size": data["size"],
            "x": spawn_x,
            "y": spawn_y
        }, to=data["campaign_code"])

    @socketio.on("get_tokens")
    def handle_get_tokens(data):
        state = game_states_dict[data["campaign_code"]]
        tokens = state.tokens.values()
        
        emit("tokens_sync", [
            normalize_token(token)
            for token in tokens
        ])
