import time

from models.events.events import MoveTokenEvent
from models.querys import GetArmorClass
__START_TIME__ = time.perf_counter()
from models.events.EventDispatcher import EventDispatcher
from services.section_service import SectionService
from services.token_service import TokenService
from world.infrastructure.MySQLTokenRepository import MySQLTokenRepository 
from campaigns.infrastructure.mysql_campaign_repository import MySQLCampaignRepository
from services.campaign_service import CampaignService
from services.character_repository import CharacterRepository
from services.character_service import CharacterService
from world.infrastructure.MySQLWorldRepository import MySQLWorldRepository
from uuid import UUID
from flask import Flask, g, make_response, redirect, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, emit

# Repositories & Services
from services.auth_service import AuthService
from services.db_service import  create_db_service
from auth.infrastructure.user_repository import MySQLUserRepository
from auth.infrastructure.auth_session_repository import MySQLAuthSessionRepository
from services.service_validator import DBSessionValidator
from auth.infrastructure.bcrypt_hasher import BcryptPasswordHasher
from world.infrastructure.MySQLSectionRepository import MySQLSectionRepository
from world.ports.section_repository import SectionRepository
# Blueprints
from routes.races import races_bp
from routes.dnd_clasess import classes_bp
from routes.characters import character_bp
from routes.campaign_routes import campaign_bp
# Utils
from services.world_service import WorldService
from utils.gen_code import generate_campaign_code
from utils.game_state_builder import build_game_state

from models.events.GameState import GameState
connected_clients = {}
campaigns = {}
worlds = {}
socket_campaigns: dict[str, str] = {}

game_states: dict[str, GameState] = {}

# ==========================
# App setup
# ==========================
app = Flask(
    __name__,
    static_folder='static',
    static_url_path='',
    template_folder='templates'
)

# ==========================
# CORS
# ==========================
CORS(app)

# ==========================
# SocketIO
# ==========================
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    manage_session=False
)

# ==========================
# Blueprints
# ==========================
app.register_blueprint(races_bp, url_prefix="/api/races")
app.register_blueprint(classes_bp, url_prefix="/api/classes")
app.register_blueprint(character_bp, url_prefix="/api/character")
app.register_blueprint(campaign_bp, url_prefix="/api/campaigns")
# ==========================
# Dependency wiring
# ==========================
db = create_db_service()

user_repo = MySQLUserRepository(db)
session_repo = MySQLAuthSessionRepository(db)
session_validator = DBSessionValidator(session_repo)
password_hasher = BcryptPasswordHasher()
auth_service = AuthService(user_repo, session_repo, password_hasher)
character_repo = CharacterRepository()
character_service = CharacterService(character_repo)
campaign_repo = MySQLCampaignRepository(db)
campaign_service = CampaignService(campaign_repo)

world_repo = MySQLWorldRepository(db)
world_service = WorldService(world_repo)
section_repo = MySQLSectionRepository(db)
section_service = SectionService(section_repo)

token_repo = MySQLTokenRepository(db)  
token_service = TokenService(token_repo)

def get_character_id(players: list[dict], my_user_id: str) -> str | None:
    for p in players:
        if p["user_id"] == my_user_id:
            return p["character_uuid"]
    return None

def get_game_state(campaign_code: str) -> GameState:
    if campaign_code not in game_states:
        game_states[campaign_code] = build_game_state(campaign_code, campaigns, character_repo)
    return game_states[campaign_code]


@app.before_request
def auth_middleware():
    sid = request.cookies.get("session_id")
    if not sid:
        g.user_id = None
        return

    try:
        g.user_id = session_validator.validate(UUID(sid))
    except Exception:
        # invalid UUID or session
        g.user_id = None

@app.before_request
def inject_services():
    g.auth_service = auth_service
    g.character_service = character_service
    g.auth_service = auth_service
    g.campaign_service = campaign_service
    g.world_service = world_service
    g.section_service = section_service
    g.token_service = token_service

@app.context_processor
def inject_user():
    user = None
    if getattr(g, "user_id", None):
        user = auth_service.get_user_by_id(g.user_id)
    return {"user": user}


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # POST
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return render_template("login.html", error="Email and password are required"), 400

    try:
        session = auth_service.login(email, password)
    except ValueError:
        return render_template("login.html", error="Invalid credentials"), 401

    # Guardamos cookie con session_id
    resp = make_response(redirect("/dashboard"))  # ruta del dashboard
    resp.set_cookie(
        "session_id",
        str(session.id),
        httponly=True,
        samesite="Lax"
    )
    return resp
    

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    # Capturar campos
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    terms = request.form.get("terms")  # checkbox

    # Validaciones básicas
    if not username or not email or not password or not confirm_password:
        return render_template("register.html", error="Todos los campos son obligatorios")
    
    if password != confirm_password:
        return render_template("register.html", error="Las contraseñas no coinciden")

    if not terms:
        return render_template("register.html", error="Debes aceptar los términos")

    try:
        # Registrar usuario
        user = auth_service.register(username=username, email=email, password=password)
    except ValueError as e:
        return render_template("register.html", error=str(e))

    try:
        # Crear sesión automáticamente
        session = auth_service.login(email=email, password=password)
    except ValueError as e:
        return render_template("register.html", error="No se pudo iniciar sesión: " + str(e))

    # Redirigir con cookie
    resp = make_response(redirect("/dashboard"))
    resp.set_cookie(
        "session_id",
        str(session.id),
        httponly=True,
        samesite="Lax"
    )
    return resp

@app.route("/logout")
def logout():
    session_id = request.cookies.get("session_id")
    if session_id:
        try:
            # Opcional: revocar la sesión en el backend
            auth_service.session_repo.revoke(UUID(session_id))
        except Exception:
            pass  # si falla, ignoramos

    # Eliminar la cookie y redirigir a login
    resp = make_response(redirect("/login"))
    resp.set_cookie("session_id", "", expires=0)
    return resp

@app.route("/dashboard")
def dashboard():
    session_id = request.cookies.get("session_id")
    if not session_id:
        return redirect("/login")  # no hay sesión

    # Buscar sesión
    session = auth_service.session_repo.get(UUID(session_id))
    if not session or session.revoked:
        return redirect("/login")

    # Obtener usuario
    user = auth_service.user_repo.get_by_id(session.user_id)
    if not user:
        return redirect("/login")

    # Obtener personajes del usuario
    characters = character_repo.get_by_owner(str(user.id))  # lista de dicts
    campaigns = campaign_repo.get_by_owner(str(user.id))  # lista de dicts

    return render_template("dashboard.html", user=user, characters=characters, campaigns=campaigns)

@app.route("/create_char")
def create_char():
    return render_template("create_char.html")

@app.route("/create_campaign")
def create_campaign_view():
    return render_template("create_campaign.html")


@app.route("/lobby/<code>", methods=["GET"])
def lobby(code):
    campaign_id = request.args.get("campaign_id")
    if not campaign_id:
        return "Campaign ID is required", 400

    return render_template("lobby.html", code=code, campaign_id=campaign_id)

@app.route("/world/<campaign_id>")
def world_view(campaign_id):
    if campaign_id not in worlds:
        return "World not initialized", 404

    world = worlds[campaign_id]
    scene = next(iter(world.scenes.values()))

    return render_template(
        "world.html",
        world=world,
        scene=scene
    )


# Nueva ruta para iniciar campaña
@app.route("/campaign/<campaign_id>/start")
def start_campaign(campaign_id):
    # Buscar sesión
    session_id = request.cookies.get("session_id")
    if not session_id:
        return redirect("/login")

    session = auth_service.session_repo.get(UUID(session_id))
    if not session or session.revoked:
        return redirect("/login")

    user = auth_service.user_repo.get_by_id(session.user_id)
    if not user:
        return redirect("/login")

    # 🔒 Obtener o reutilizar lobby
    lobby_code = get_or_create_lobby(campaign_id)
    return render_template(
        "lobby.html",
        code=lobby_code,
        dm=True,
        campaign_id=campaign_id,
        characters=None
    )

def get_or_create_lobby(campaign_id: str) -> str:
    for code, lobby in campaigns.items():
        if lobby["campaign_id"] == campaign_id:
            return code

    # No existe → crear
    code = generate_campaign_code()
    campaigns[code] = {
        "campaign_id": campaign_id,
        "players": {}
    }
    return code

@app.route("/join/<code>")
def join_lobby(code):
    # Validar lobby
    if code not in campaigns:
        return "Lobby not found", 404

    # Buscar sesión
    session_id = request.cookies.get("session_id")
    if not session_id:
        return redirect("/login")

    session = auth_service.session_repo.get(UUID(session_id))
    if not session or session.revoked:
        return redirect("/login")

    # Obtener usuario
    user = auth_service.user_repo.get_by_id(session.user_id)
    if not user:
        return redirect("/login")

    # Obtener campaña
    campaign_id = campaigns[code]["campaign_id"]

    # Obtener personajes del usuario
    characters = character_repo.get_by_owner(str(user.id))  # lista de dicts



    return render_template(
        "lobby.html",
        code=code,
        dm=False,
        campaign_id=campaign_id,
        characters=characters
    )


@app.route("/game")
def game():
    code = request.args.get("code")
    if not code or code not in campaigns:
        return "Campaña no válida", 404

    campaign_id = campaigns[code]["campaign_id"]
    campaign_instance = campaign_repo.get_by_id(campaign_id)
    if not campaign_instance:
        return "Campaña no encontrada", 404 
    
    world = world_repo.get(campaign_instance["world_id"])
    if not world:    
        return "Mundo no encontrado", 404
    
    session_id = request.cookies.get("session_id")
    if not session_id:
        return redirect("/login")

    # Buscar sesión
    session = auth_service.session_repo.get(UUID(session_id))
    if not session or session.revoked:
        return redirect("/login")
    user_id = str(session.user_id)
    if not user_id:
        return redirect("/login")

    world = world_repo.get(campaign_instance["world_id"])
    campaign_model = campaigns[code]
    
    players = [
        {
            "user_id": p["user_id"],
            "username": p["username"],
            "character_uuid": p["character_uuid"],
            "is_dm": p["is_dm"]
        }
        for p in campaign_model["players"].values()
    ]
    current_scene = world.scenes[0] # type: ignore
    my_character_id = get_character_id(players, user_id)
    tokens = []
    my_token = None
    game_state = get_game_state(code)

    for p in players:
        character_id = p.get("character_uuid")
        if not character_id:
            continue

        token = g.token_service.get_by_character(UUID(character_id))
        if not token:
            continue
        
        tokens.append(token)
        game_state.add_token(token)
        if character_id == my_character_id:
            my_token = token
    current_section = current_scene.sections[0] if current_scene.sections else None  # type: ignore
    is_dm = any(p["is_dm"] and p["user_id"] == user_id for p in players)
    
    return render_template(
        "game.html",
        code=code,
        players=players,
        campaign_model=campaign_model, 
        world=world,
        my_character_id=my_character_id,
        current_scene={
            "id": str(current_scene.id),
            "name": current_scene.name,
            "map_url": current_scene.map_url
        },
        tokens=tokens,
        my_token=my_token if my_token else None,
        is_dm=is_dm,
        current_section = current_section.to_dict() if current_section else None
    )

# ========================================
# WEBSOCKET HANDLERS
# ========================================

@socketio.on("connect")
def handle_connect():
    sid = request.sid  # type: ignore
    
    connected_clients[sid] = {
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
    if code not in campaigns:
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
    socket_campaigns[request.sid] = code #type: ignore
    user_id = str(user.id)
    campaign_id = campaigns[code]["campaign_id"]
    # determinar DM
    campaign = campaign_repo.get_by_id(campaign_id)
    is_dm = campaign and str(campaign["owner_id"]) == user_id

    players = campaigns[code]["players"]

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
    campaign = campaigns.get(code)

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
    
    # Campaña válida → todos entran al juego
    emit(
        "campaign_started",
        {"code": code},
        to=code
    )


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid  # type: ignore
    
    if sid in connected_clients:
        del connected_clients[sid]

@socketio.on("select_character")
def handle_select_character(data):
    code = data.get("code")
    character_uuid = data.get("character_uuid")
    sid = request.sid  # type: ignore

    if code not in campaigns:
        return

    for player in campaigns[code]["players"].values():
        if player["sid"] == sid:
            character = character_repo.get_by_id(character_uuid)
            if not character:
                return

            player["character_uuid"] = character_uuid
            player["character_name"] = character["name"]
            break

    emit(
        "player_joined",
        {"players": list(campaigns[code]["players"].values())},
        to=code
    )


@socketio.on("chat_message")
def handle_chat_message(data):
    print("Mensaje recibido:", data)
    code = data.get("code")
    text = data.get("text", "").strip()
    sid = request.sid  # type: ignore

    if not text or code not in campaigns:
        return

    sender = "Desconocido"

    for player in campaigns[code]["players"].values():
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

    campaign_code = socket_campaigns.get(request.sid) #type: ignore
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
        print("Error al calcular AC:")
        traceback.print_exc()
        emit("error", {"message": str(e)})
        return
    print(f"AC result for actor {actor_id}: {result.value} (breakdown: {result.breakdown})")
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

    state = game_states[campaign_code]
    event = MoveTokenEvent(token_id=token_id, x=x, y=y) # type: ignore
    print(token_id, x, y)
    try:
        state.dispatch(event)

        emit("token_moved", {
            "token_id": token_id,
            "x": x,
            "y": y
        }, to=campaign_code)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        emit("error", {"message": str(e)})


startup_time = time.perf_counter() - __START_TIME__
print(f"[BOOT] Startup time: {startup_time:.3f}s")
socketio.run(
    app=app, 
    host='0.0.0.0',
    port=5000,
    debug=True,
    allow_unsafe_werkzeug=True
)