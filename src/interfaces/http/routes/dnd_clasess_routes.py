from flask import Blueprint, request, jsonify
from src.core.character.dndclass import CLASS_MAP
classes_bp = Blueprint("classes", __name__)


@classes_bp.route("/attributes")
def class_attributes():
    class_name = request.args.get("class")

    if class_name not in CLASS_MAP:
        return jsonify({"error": "Clase no válida"}), 400

    class_instance = CLASS_MAP[class_name]()

    return jsonify({
        "name": class_instance.name,
        "description": class_instance.definition,
        "hit_die": class_instance.hit_die,

        # Competencias estructurales
        "skill_choices": class_instance.skill_choices,
        "skill_choices_count": class_instance.skill_choices_count,
        "saving_throw_proficiencies": class_instance.saving_throw_proficiencies,
        "weapon_proficiencies": class_instance.weapon_proficiencies,
        "armor_proficiencies": class_instance.armor_proficiencies,

        # Features
        "special_features": class_instance.features_info_by_level(),
    })

@classes_bp.route("/all")
def all_classes():
    result = {}

    for key, cls in CLASS_MAP.items():
        instance = cls()

        result[key] = {
            "name": instance.name,
            "description": instance.definition,
            "hit_die": instance.hit_die,

            # Competencias estructurales
            "skill_choices": instance.skill_choices,
            "skill_choices_count": instance.skill_choices_count,
            "saving_throw_proficiencies": instance.saving_throw_proficiencies,
            "weapon_proficiencies": instance.weapon_proficiencies,
            "armor_proficiencies": instance.armor_proficiencies,

            # Features
            "special_features": instance.features_info_by_level(),
        }

    return jsonify(result)
