from uuid import UUID
from flask import Blueprint, request, jsonify
from services.campaign_service import CampaignService
from campaigns.infrastructure.mysql_campaign_repository import MySQLCampaignRepository
from services.db_service import DatabaseService
from auth.infrastructure.auth_session_repository import MySQLAuthSessionRepository
from auth.infrastructure.user_repository import MySQLUserRepository
from auth.infrastructure.bcrypt_hasher import BcryptPasswordHasher
from services.auth_service import AuthService

campaign_bp = Blueprint("campaign", __name__, url_prefix="/campaign")

# ------------------------
# Infra
# ------------------------
db = DatabaseService()

campaign_repo = MySQLCampaignRepository(db)
campaign_service = CampaignService(campaign_repo)

user_repo = MySQLUserRepository(db)
session_repo = MySQLAuthSessionRepository(db)
password_hasher = BcryptPasswordHasher()
auth_service = AuthService(user_repo, session_repo, password_hasher)

# ------------------------
# Helpers
# ------------------------
def get_current_user_id() -> UUID | None:
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    session = auth_service.session_repo.get(UUID(session_id))
    if not session or session.revoked:
        return None

    return session.user_id


@campaign_bp.route("/create", methods=["POST"])
def create_campaign():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    data = request.json or {}
    name = data.get("name")

    if not name:
        return jsonify({"error": "Nombre requerido"}), 400

    campaign = campaign_service.create(user_id, name)

    return jsonify({
        "id": str(campaign.id),
        "name": campaign.name
    }), 201

@campaign_bp.route("/join", methods=["POST"])
def join_campaign():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    data = request.json or {}
    campaign_id = data.get("campaign_id")

    if not campaign_id:
        return jsonify({"error": "campaign_id requerido"}), 400

    try:
        campaign_service.join(UUID(campaign_id), user_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"status": "joined"}), 200

@campaign_bp.route("/my-campaigns", methods=["GET"])
def my_campaigns():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    campaigns = campaign_service.get_by_user(user_id)
    return jsonify([c.to_dict(c) for c in campaigns]), 200

@campaign_bp.route("/load", methods=["GET"])
def load_campaign():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401

    campaign_id = request.args.get("id")
    if not campaign_id:
        return jsonify({"error": "ID requerido"}), 400

    campaign = campaign_service.load(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaña no encontrada"}), 404

    if not campaign_repo.is_member(UUID(campaign_id), user_id):
        return jsonify({"error": "Acceso denegado"}), 403

    return jsonify(campaign.to_dict(campaign)), 200
