from uuid import UUID
from flask import Blueprint, request, jsonify, g

character_bp = Blueprint("character", __name__)

# =====================================
# Helpers (sin lógica pesada)
# =====================================

def get_character_service():
    return g.character_service


def get_auth_service():
    return g.auth_service

def get_token_service():    
    return g.token_service
def get_current_user_id() -> str | None:
    """
    Obtiene el user_id a partir de la cookie session_id.
    No crea servicios. No toca DB fuera del request.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    auth_service = get_auth_service()
    session = auth_service.session_repo.get(UUID(session_id))

    if not session or session.revoked:
        return None

    return str(session.user_id)


# =====================================
# Routes
# =====================================

@character_bp.post("/create")
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
        character = get_character_service().create(
            UUID(owner_id),
            name,
            race_key,
            class_key
        )

        # -------- CREATE TOKEN --------
        try:
            get_token_service().create(
                character_id=character.id,
                x=0,
                y=0,
                size=(1, 1),
                owner_user_id=UUID(owner_id),
                is_visible=True,
                label=character.name,
            )
            print("Token creado para personaje:", character.name)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("Error al crear token para personaje:", e)
    except KeyError:
        return jsonify({"error": "Raza o clase inválida"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "id": str(character.id),
        "character": character.to_json()
    }), 201



@character_bp.get("/load")
def load_character():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    character_id = request.args.get("from_id")
    if not character_id:
        return jsonify({"error": "ID requerido"}), 400

    character = get_character_service().load(character_id)
    if not character:
        return jsonify({"error": "Personaje no encontrado"}), 404

    if str(character.owner_id) != owner_id:
        return jsonify({"error": "Acceso denegado"}), 403

    return jsonify(character.to_json()), 200


@character_bp.get("/my-characters")
def my_characters():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    characters = get_character_service().get_by_owner(owner_id)
    return jsonify(characters), 200
