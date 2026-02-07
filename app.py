from uuid import UUID
from flask import Flask, g, make_response, redirect, render_template, request, send_from_directory, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit

# Repositories & Services
from services.auth_service import AuthService
from services.db_service import DatabaseService
from auth.infrastructure.user_repository import MySQLUserRepository
from auth.infrastructure.auth_session_repository import MySQLAuthSessionRepository
from services.service_validator import DBSessionValidator
from auth.ports.password_hasher import PasswordHasher
from auth.infrastructure.bcrypt_hasher import BcryptPasswordHasher

# Blueprints
from routes.races import races_bp
from routes.dnd_clasess import classes_bp
from routes.characters import character_bp, repo as character_repo
from routes.campaign_routes import campaign_bp, campaign_repo
# Utils
from utils.gen_code import generate_campaign_code

import os

connected_clients = {}
campaigns = {}

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
db = DatabaseService()

user_repo = MySQLUserRepository(db)
session_repo = MySQLAuthSessionRepository(db)

session_validator = DBSessionValidator(session_repo)
password_hasher = BcryptPasswordHasher()
auth_service = AuthService(user_repo, session_repo, password_hasher)

# ==========================
# Auth middleware
# ==========================
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
    
from flask import request, render_template, redirect, make_response

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


    return render_template("dashboard.html", user=user, characters=characters)


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

@app.route('/<path:path>')
def catch_all(path):
    """Catch-all para React Router y archivos estáticos"""
    # Si el archivo existe en static, sírvelo
    if os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    # Si no, sirve index.html (para rutas de React Router)
    return send_from_directory('static', 'index.html')

# ========================================
# API REST (nuevas rutas para React)
# ========================================

@app.route('/api/campaigns', methods=['POST'])
def create_campaign_rest():
    """Endpoint REST para crear campaña (usado por React Index)"""
    code = generate_campaign_code()
    campaigns[code] = {
        "name": "Nueva Campaña",
        "players": {}
    }
    
    return jsonify({
        'campaign_id': code,
        'role': 'dm'
    })

@app.route('/api/campaigns/join', methods=['POST'])
def join_campaign_rest():
    """Endpoint REST para validar código de campaña"""
    data = request.get_json()
    code = data.get('code', '').upper()
    
    if code not in campaigns:
        return jsonify({'error': 'Campaña no encontrada'}), 404
    
    return jsonify({
        'campaign_id': code,
        'role': 'player'
    })

@app.route("/api/connected_clients")
def get_connected_clients():
    return {
        "count": len(connected_clients),
        "clients": list(connected_clients.keys())
    }

# ========================================
# RUTAS HTML LEGACY (puedes mantenerlas o eliminarlas)
# ========================================

@app.route("/card")
def card():
    return render_template("card.html")

@app.route("/create_char")
def create_char():
    return render_template("create_char.html")

@app.route("/lobby-old")  # Renombrado para no conflictuar
def lobby_old():
    """Lobby antiguo (Jinja). Puedes eliminarlo cuando migres a React"""
    return render_template("lobby.html")

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

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid  # type: ignore
    
    if sid in connected_clients:
        del connected_clients[sid]

@socketio.on("create_campaign")
def handle_create_campaign(data):
    dm_username = data.get("username", "Dungeon Master")
    campaign_name = data.get("name", "Campaña sin nombre")
    sid = request.sid  # type: ignore

    code = generate_campaign_code()
    campaigns[code] = {
        "name": campaign_name,
        "players": {}
    }

    connected_clients[sid]['username'] = dm_username

    emit("campaign_created", {
        "code": code,
        "name": campaign_name
    })

@socketio.on("join_campaign")
def handle_join_campaign(data):
    code = data.get("code")
    username = data.get("username")
    character_uuid = data.get("character_uuid")
    sid = request.sid  # type: ignore

    if code not in campaigns:
        emit("error", {"message": "Campaña no encontrada"})
        return

    join_room(code)
    
    campaigns[code]["players"][sid] = {
        "username": username,
        "character_uuid": character_uuid
    }
    connected_clients[sid]['username'] = username

    all_participants = [
        {
            "username": p["username"],
            "character_uuid": p.get("character_uuid"),
            "is_dm": p["username"] == "Dungeon Master"
        } for p in campaigns[code]["players"].values()
    ]

    emit("player_joined", {
        "players": all_participants,
        "new_player": username
    }, to=code)

@socketio.on("leave_campaign")
def handle_leave_campaign(data):
    code = data.get("code")
    sid = request.sid  # type: ignore

    if code in campaigns and sid in campaigns[code]["players"]:
        username = campaigns[code]["players"][sid]["username"]
        del campaigns[code]["players"][sid]
        leave_room(code)

        all_participants = [{
            "username": campaigns[code]["dm_username"],
            "character_uuid": None,
            "is_dm": True
        }]
        
        all_participants.extend([
            {
                "username": p["username"],
                "character_uuid": p.get("character_uuid"),
                "is_dm": False
            } for p in campaigns[code]["players"].values()
        ])

        emit("player_left", {
            "username": username,
            "players": all_participants
        }, to=code)

@socketio.on("chat_message")
def handle_chat_message(data):
    code = data.get("code")
    text = data.get("text", "").strip()
    sid = request.sid  # type: ignore

    if not text or code not in campaigns:
        return

    if sid in campaigns[code]["players"]:
        sender = campaigns[code]["players"][sid]["username"]
    else:
        sender = "Desconocido"

    emit("chat_message", {
        "sender": sender,
        "text": text
    }, to=code)


if __name__ == "__main__":
    socketio.run(
        app=app, 
        host='0.0.0.0',
        debug=True,
        port=5000,
        allow_unsafe_werkzeug=True
    )