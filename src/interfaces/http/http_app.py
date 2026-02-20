import os
from uuid import UUID
from flask import Flask, g, make_response, redirect, render_template, request
from flask_cors import CORS
import time

# Blueprints
from src.interfaces.http.routes.races_routes import races_bp
from src.interfaces.http.routes.dnd_clasess_routes import classes_bp
from src.interfaces.http.routes.characters_routes import character_bp
from src.interfaces.http.routes.campaign_routes import campaign_bp
from src.interfaces.http.routes.enemies_routes import enemy_bp
from src.shared.utils.game_state_builder import build_game_state
# Services
from src.features.auth.application.auth_service import AuthService
from src.shared.database.db_service import create_db_service
from src.features.auth.infrastructure.auth_session_repository import MySQLAuthSessionRepository
from src.features.auth.infrastructure.user_repository import MySQLUserRepository
from src.shared.validators.service_validator import DBSessionValidator
from src.features.auth.infrastructure.bcrypt_hasher import BcryptPasswordHasher
from src.features.characters.infrastructure.character_repository import CharacterRepository
from src.features.characters.application.character_service import CharacterService
from src.features.campaigns.infrastructure.mysql_campaign_repository import MySQLCampaignRepository
from src.features.campaigns.application.campaign_service import CampaignService
from src.features.world.infrastructure.MySQLWorldRepository import MySQLWorldRepository
from src.features.world.application.world_service import WorldService
from src.features.world.infrastructure.MySQLSectionRepository import MySQLSectionRepository
from src.features.world.application.section_service import SectionService
from src.features.world.infrastructure.MySQLTokenRepository import MySQLTokenRepository
from src.features.world.application.token_service import TokenService

# Utils
from src.shared.utils.gen_code import generate_campaign_code
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def create_app(campaigns_dict: dict, worlds_dict: dict, game_states_dict: dict):
    """
    Factory function to create and configure the Flask app
    
    Args:
        campaigns_dict: Shared dictionary for campaign data
        worlds_dict: Shared dictionary for world data
        game_states_dict: Shared dictionary for game states
    """
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, 'public', 'static'),
        static_url_path='',
        template_folder=os.path.join(BASE_DIR, 'public', 'templates')
    )
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

    # CORS
    CORS(app)

    # Register Blueprints
    app.register_blueprint(races_bp, url_prefix="/api/races")
    app.register_blueprint(classes_bp, url_prefix="/api/classes")
    app.register_blueprint(character_bp, url_prefix="/api/character")
    app.register_blueprint(campaign_bp, url_prefix="/api/campaigns")
    app.register_blueprint(enemy_bp, url_prefix="/api/enemies")

    # Initialize dependencies
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

    # Store shared dictionaries in app config
    app.config['CAMPAIGNS'] = campaigns_dict
    app.config['WORLDS'] = worlds_dict
    app.config['GAME_STATES'] = game_states_dict

    # Middleware
    @app.before_request
    def auth_middleware():
        sid = request.cookies.get("session_id")
        if not sid:
            g.user_id = None
            return

        try:
            g.user_id = session_validator.validate(UUID(sid))
        except Exception:
            g.user_id = None

    @app.before_request
    def inject_services():
        g.auth_service = auth_service
        g.character_service = character_service
        g.campaign_service = campaign_service
        g.world_service = world_service
        g.section_service = section_service
        g.token_service = token_service
    app.extensions["services"] = {
        "auth_service": auth_service,
        "character_service": character_service,
        "campaign_service": campaign_service,
        "world_service": world_service,
        "section_service": section_service,
        "token_service": token_service
    }
    app.extensions["repos"] = {
        "user_repo": user_repo,
        "session_repo": session_repo,
        "character_repo": character_repo,
        "campaign_repo": campaign_repo,
        "world_repo": world_repo,
        "section_repo": section_repo,
        "token_repo": token_repo
    }

    @app.context_processor
    def inject_user():
        user = None
        if getattr(g, "user_id", None):
            user = auth_service.get_user_by_id(g.user_id)
        return {"user": user}

    # Helper functions
    def get_character_id(players: list[dict], my_user_id: str) -> str | None:
        for p in players:
            if p["user_id"] == my_user_id:
                return p["character_uuid"]
        return None

    def get_or_create_lobby(campaign_id: str) -> str:
        for code, lobby in campaigns_dict.items():
            if lobby["campaign_id"] == campaign_id:
                return code

        code = generate_campaign_code()
        campaigns_dict[code] = {
            "campaign_id": campaign_id,
            "players": {}
        }
        return code

    # Routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template("login.html", error="Email and password are required"), 400

        try:
            session = auth_service.login(email, password)
        except ValueError:
            return render_template("login.html", error="Invalid credentials"), 401

        resp = make_response(redirect("/dashboard"))
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

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        terms = request.form.get("terms")

        if not username or not email or not password or not confirm_password:
            return render_template("register.html", error="Todos los campos son obligatorios")

        if password != confirm_password:
            return render_template("register.html", error="Las contraseñas no coinciden")

        if not terms:
            return render_template("register.html", error="Debes aceptar los términos")

        try:
            user = auth_service.register(username=username, email=email, password=password)
        except ValueError as e:
            return render_template("register.html", error=str(e))

        try:
            session = auth_service.login(email=email, password=password)
        except ValueError as e:
            return render_template("register.html", error="No se pudo iniciar sesión: " + str(e))

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
                auth_service.session_repo.revoke(UUID(session_id))
            except Exception:
                pass

        resp = make_response(redirect("/login"))
        resp.set_cookie("session_id", "", expires=0)
        return resp

    @app.route("/dashboard")
    def dashboard():
        session_id = request.cookies.get("session_id")
        if not session_id:
            return redirect("/login")

        session = auth_service.session_repo.get(UUID(session_id))
        if not session or session.revoked:
            return redirect("/login")

        user = auth_service.user_repo.get_by_id(session.user_id)
        if not user:
            return redirect("/login")

        characters = character_repo.get_by_owner(str(user.id))
        campaigns = campaign_repo.get_by_owner(str(user.id))

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
        if campaign_id not in worlds_dict:
            return "World not initialized", 404

        world = worlds_dict[campaign_id]
        scene = next(iter(world.scenes.values()))

        return render_template(
            "world.html",
            world=world,
            scene=scene
        )

    @app.route("/campaign/<campaign_id>/start")
    def start_campaign(campaign_id):
        session_id = request.cookies.get("session_id")
        if not session_id:
            return redirect("/login")

        session = auth_service.session_repo.get(UUID(session_id))
        if not session or session.revoked:
            return redirect("/login")

        user = auth_service.user_repo.get_by_id(session.user_id)
        if not user:
            return redirect("/login")

        lobby_code = get_or_create_lobby(campaign_id)
        return render_template(
            "lobby.html",
            code=lobby_code,
            dm=True,
            campaign_id=campaign_id,
            characters=None
        )

    @app.route("/join/<code>")
    def join_lobby(code):
        if code not in campaigns_dict:
            return "Lobby not found", 404

        session_id = request.cookies.get("session_id")
        if not session_id:
            return redirect("/login")

        session = auth_service.session_repo.get(UUID(session_id))
        if not session or session.revoked:
            return redirect("/login")

        user = auth_service.user_repo.get_by_id(session.user_id)
        if not user:
            return redirect("/login")

        campaign_id = campaigns_dict[code]["campaign_id"]
        characters = character_repo.get_by_owner(str(user.id))
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
        if not code or code not in campaigns_dict:
            return "Campaña no válida", 400
        response = render_template(
            "game.html",
            code=code,
        )
        return response

    
    @app.route('/storage/<path:filename>')
    def serve_storage(filename):
        from flask import send_from_directory, abort
        import os
        
        # BASE_DIR apunta a la raíz del proyecto
        storage_dir = os.path.join(BASE_DIR, 'storage', 'uploads')
        
        # filename ya viene como: "uploads/maps/file.jpg" o "maps/file.jpg"
        # Necesitamos solo: "maps/file.jpg"
        clean_filename = filename
        if clean_filename.startswith('uploads/'):
            clean_filename = clean_filename[8:]  # Remover "uploads/"
        
        full_path = os.path.join(storage_dir, clean_filename)
    

        return send_from_directory(storage_dir, clean_filename)
    return app