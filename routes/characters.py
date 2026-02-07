from uuid import UUID   
from flask import Blueprint, request, jsonify, render_template, g
from auth.infrastructure.auth_session_repository import MySQLAuthSessionRepository
from auth.infrastructure.bcrypt_hasher import BcryptPasswordHasher
from auth.infrastructure.user_repository import MySQLUserRepository
from services.character_service import CharacterService
from services.character_repository import CharacterRepository
from services.auth_service import AuthService
from auth.ports.auth_session_repository import AuthSessionRepository
from auth.domain.auth_session import AuthSession
from services.db_service import DatabaseService
from services.service_validator import DBSessionValidator

character_bp = Blueprint("character", __name__) 

repo = CharacterRepository()
service = CharacterService(repo)
db = DatabaseService()

user_repo = MySQLUserRepository(db)
session_repo = MySQLAuthSessionRepository(db)

session_validator = DBSessionValidator(session_repo)
password_hasher = BcryptPasswordHasher()
auth_service = AuthService(user_repo, session_repo, password_hasher)

def get_current_user_id() -> str | None:
    """Obtiene el owner_id a partir de la cookie session_id"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    session = auth_service.session_repo.get(UUID(session_id))
    if not session or session.revoked:
        return None
    return str(session.user_id)


@character_bp.route("/create", methods=["POST"])
def create_character():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401
    
    data = request.json or {}
    name = data.get("name")
    race_key = data.get("race")
    class_key = data.get("class")

    if not name or not race_key or not class_key:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        character = service.create(UUID(owner_id), name, race_key, class_key)
    except KeyError:
        return jsonify({"error": "Raza o clase inválida"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "id": character.id,
        "character": character.to_json()
    }), 201


@character_bp.route("/load", methods=["GET"])
def load_character():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    from_id = request.args.get("from_id")
    if not from_id:
        return jsonify({"error": "ID requerido"}), 400

    character = service.load(from_id)
    if not character:
        return jsonify({"error": "Personaje no encontrado"}), 404

    # Verificar que el personaje pertenece al usuario
    if character.owner_id != owner_id:
        return jsonify({"error": "Acceso denegado"}), 403

    return jsonify(character), 200


@character_bp.route("/my-characters", methods=["GET"])
def my_characters():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    characters = repo.get_by_owner(owner_id)
    return jsonify(characters), 200
