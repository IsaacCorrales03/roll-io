from flask import Flask, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit
from routes.races import races_bp
from routes.dnd_clasess import classes_bp
from routes.characters import character_bp
from utils.gen_code import generate_campaign_code

app = Flask(__name__)
app.register_blueprint(races_bp, url_prefix="/api/races")
app.register_blueprint(classes_bp, url_prefix="/api/classes")
app.register_blueprint(character_bp, url_prefix="/api/character")
app.static_folder = './static'

CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    manage_session=False
)

connected_clients = {}
campaigns = {}

@socketio.on("connect")
def handle_connect():
    sid = request.sid  # type: ignore
    print(f"✓ Cliente conectado - SID: {sid}")
    
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
    print(f"✗ Cliente desconectado - SID: {sid}")
    
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
        "players": {}  # Todos son jugadores, incluido el DM
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

    # TODOS se unen igual, incluido el DM
    join_room(code)
    
    campaigns[code]["players"][sid] = {
        "username": username,
        "character_uuid": character_uuid
    }
    connected_clients[sid]['username'] = username

    # Construir lista de jugadores
    all_participants = [
        {
            "username": p["username"],
            "character_uuid": p.get("character_uuid"),
            "is_dm": p["username"] == "Dungeon Master"  # Identificar DM por nombre
        } for p in campaigns[code]["players"].values()
    ]

    # Emitir a toda la sala
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

        # Reconstruir lista
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

    # Obtener el nombre del jugador
    if sid in campaigns[code]["players"]:
        sender = campaigns[code]["players"][sid]["username"]
    else:
        sender = "Desconocido"

    # Emitir mensaje a todos en la sala
    emit("chat_message", {
        "sender": sender,
        "text": text
    }, to=code)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/card")
def card():
    return render_template("card.html")

@app.route("/create_char")
def create_char():
    return render_template("create_char.html")

@app.route("/api/connected_clients")
def get_connected_clients():
    return {
        "count": len(connected_clients),
        "clients": list(connected_clients.keys())
    }

@app.route("/lobby")
def lobby():
    """
    Página del lobby de la campaña.
    Query params esperados:
      - campaign: código de la campaña
      - uuid (opcional): UUID del personaje del jugador
    """
    return render_template("lobby.html")

if __name__ == "__main__":
    socketio.run(
        app=app, 
        host='0.0.0.0',
        debug=True,
        port=5000,
        allow_unsafe_werkzeug=True
    )