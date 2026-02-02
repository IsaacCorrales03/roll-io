from flask import Blueprint, request, jsonify
from models.races import *
races_bp = Blueprint("races", __name__)

@races_bp.route("/attributes")
def race_attributes():
    race_name = request.args.get("race")
    if race_name not in RACE_MAP:
        return jsonify({"error": "Raza no válida"}), 400
    race_instance = RACE_MAP[race_name]
    return jsonify({
        "name": race_instance.name,
        "description": race_instance.description,
        "base_attributes": race_instance.attributes,
        "racial_bonus_stats":race_instance.racial_bonus_stats,
        "special_traits": race_instance.special_traits
    })

@races_bp.route("/all")
def all_races():
    return jsonify({
        key: {
            "name": race.name,
            "description": race.description,
            "base_attributes": race.attributes,
            "racial_bonus_stats": race.racial_bonus_stats,
            "special_traits": race.special_traits
        }
        for key, race in RACE_MAP.items()
    })
