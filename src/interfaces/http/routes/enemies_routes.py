import os
import uuid
from flask import Blueprint, request, jsonify, g

enemy_bp = Blueprint("enemy", __name__)

# =========================
# Helpers
# =========================
def get_enemy_service():
    return g.enemy_service

def get_auth_service():
    return g.auth_service

def get_current_user_id() -> str | None:
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    auth_service = get_auth_service()
    session = auth_service.session_repo.get(uuid.UUID(session_id))
    if not session or session.revoked:
        return None
    return str(session.user_id)


# =========================
# Upload settings
# =========================
UPLOAD_FOLDER = "storage/uploads/enemies"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# =========================
# Routes
# =========================

@enemy_bp.post("/create")
def create_enemy():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    data = request.json or {}

    required_fields = ["name", "hp", "max_hp", "ac", "attributes"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Datos incompletos"}), 400

    try:
        enemy = get_enemy_service().create(
            owner_id=uuid.UUID(owner_id),
            name=data["name"],
            hp=data["hp"],
            max_hp=data["max_hp"],
            ac=data["ac"],
            attributes=data["attributes"],
            attacks=data.get("attacks", []),
            asset_url=data.get("asset_url"),
            size=tuple(data.get("size", (1, 1))),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"id": str(enemy.id), "enemy": enemy.to_json()}), 201


@enemy_bp.get("/load")
def load_enemy():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    enemy_id = request.args.get("enemy_id")
    if not enemy_id:
        return jsonify({"error": "ID requerido"}), 400

    enemy = get_enemy_service().load(enemy_id)
    if not enemy:
        return jsonify({"error": "Enemigo no encontrado"}), 404

    if str(enemy.owner_id) != owner_id:
        return jsonify({"error": "Acceso denegado"}), 403

    return jsonify(enemy.to_json()), 200


@enemy_bp.get("/my-enemies")
def my_enemies():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    enemies = get_enemy_service().list_by_owner(owner_id)
    return jsonify([enemy.to_json() for enemy in enemies]), 200


@enemy_bp.put("/update")
def update_enemy():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    data = request.json or {}
    enemy_id = data.get("id")
    if not enemy_id:
        return jsonify({"error": "ID requerido"}), 400

    enemy_service = get_enemy_service()
    enemy = enemy_service.load(enemy_id)
    if not enemy:
        return jsonify({"error": "Enemigo no encontrado"}), 404

    if str(enemy.owner_id) != owner_id:
        return jsonify({"error": "Acceso denegado"}), 403

    # Actualizar campos
    for key in ["name", "hp", "max_hp", "ac", "attributes", "size", "asset_url", "attacks"]:
        if key in data:
            setattr(enemy, key, data[key])

    enemy_service.save(enemy)
    return jsonify({"success": True, "enemy": enemy.to_json()}), 200


@enemy_bp.delete("/delete")
def delete_enemy():
    owner_id = get_current_user_id()
    if not owner_id:
        return jsonify({"error": "No autenticado"}), 401

    enemy_id = request.args.get("enemy_id")
    if not enemy_id:
        return jsonify({"error": "ID requerido"}), 400

    enemy_service = get_enemy_service()
    enemy = enemy_service.load(enemy_id)
    if not enemy:
        return jsonify({"error": "Enemigo no encontrado"}), 404

    if str(enemy.owner_id) != owner_id:
        return jsonify({"error": "Acceso denegado"}), 403

    deleted = enemy_service.delete(enemy_id)
    return jsonify({"success": deleted}), 200


@enemy_bp.post("/upload")
def upload_enemy_asset():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400
    if not allowed_file(file.filename): # type: ignore
        return jsonify({"success": False, "error": "Invalid type"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[1].lower()  # type: ignore
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    return jsonify({
        "success": True,
        "asset_url": f"/storage/enemies/{filename}"
    }), 200