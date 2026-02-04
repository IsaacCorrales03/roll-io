from flask import Blueprint, request, jsonify, render_template
from services.character_service import CharacterService
from services.character_repository import CharacterRepository


character_bp = Blueprint("character", __name__)

repo = CharacterRepository()
service = CharacterService(repo)


@character_bp.route("/create", methods=["POST"])
def create_character():
    name = request.args.get("name")
    race_key = request.args.get("race")
    class_key = request.args.get("class")

    if not name or not race_key or not class_key:
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        character = service.create(name, race_key, class_key)
    except KeyError:
        return jsonify({"error": "Raza o clase inválida"}), 400
    return jsonify({
        "id": character.id,
        "character": character.to_json()
    }), 201

@character_bp.route("/load", methods=["GET"])
def load_character():
    from_id = request.args.get("from_id")
    if not from_id:
        return jsonify({"error": "ID requerido"}), 400

    character = service.load(from_id)
    if character is None:
        return jsonify({"error": "Personaje no encontrado"}), 404
    print(character.to_json())
    return jsonify(character.to_json()), 200

