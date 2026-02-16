import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import uuid

enemy_bp = Blueprint("enemy", __name__)

UPLOAD_FOLDER = "storage/uploads/enemies"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@enemy_bp.post("/upload")
def upload_enemy_asset():

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Invalid type"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[1].lower() # type: ignore
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    return jsonify({
        "success": True,
        "asset_url": f"/storage/uploads/enemies/{filename}"
    })
