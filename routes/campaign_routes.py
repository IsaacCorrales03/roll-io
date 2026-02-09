from uuid import UUID
from flask import Blueprint, request, jsonify, g

campaign_bp = Blueprint("campaign", __name__, url_prefix="/campaign")

# =====================================
# Helpers (sin lógica pesada)
# =====================================

def get_campaign_service():
    return g.campaign_service


def get_world_service():
    return g.world_service


def get_auth_service():
    return g.auth_service


def get_current_user_id() -> UUID | None:
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    auth_service = get_auth_service()
    session = auth_service.session_repo.get(UUID(session_id))

    if not session or session.revoked:
        return None

    return session.user_id


# =====================================
# Routes
# =====================================

@campaign_bp.post("/create")
def create_campaign():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    data = request.json or {}

    campaign_name = data.get("campaign", {}).get("name")
    world_name = data.get("world", {}).get("name")
    world_lore = data.get("world", {}).get("lore", "")
    scene_name = data.get("scene", {}).get("name")
    scene_map = data.get("scene", {}).get("map_url")

    if not all([campaign_name, world_name, scene_name, scene_map]):
        return jsonify({"error": "Datos incompletos"}), 400

    # 1️⃣ Crear mundo + escena inicial
    world = get_world_service().create_world(
        name=world_name,
        lore=world_lore,
        initial_scene_name=scene_name,
        initial_scene_map_url=scene_map,
    )

    # 2️⃣ Crear campaña asociada
    campaign = get_campaign_service().create(
        owner_id=user_id,
        name=campaign_name,
        world_id=world.id
    )

    return jsonify({
        "id": str(campaign.id),
        "world_id": str(world.id)
    }), 201


@campaign_bp.post("/join")
def join_campaign():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    data = request.json or {}
    campaign_id = data.get("campaign_id")

    if not campaign_id:
        return jsonify({"error": "campaign_id requerido"}), 400

    try:
        get_campaign_service().join(UUID(campaign_id), user_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"status": "joined"}), 200


@campaign_bp.get("/my-campaigns")
def my_campaigns():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    campaigns = get_campaign_service().get_by_user(user_id)
    return jsonify([c.to_dict() for c in campaigns]), 200


@campaign_bp.get("/load")
def load_campaign():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    campaign_id = request.args.get("id")
    if not campaign_id:
        return jsonify({"error": "ID requerido"}), 400

    campaign = get_campaign_service().load(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaña no encontrada"}), 404

    if not get_campaign_service().is_member(UUID(campaign_id), user_id):
        return jsonify({"error": "Acceso denegado"}), 403

    return jsonify(campaign.to_dict()), 200
