from src.core.game.Event import EventDispatcher, GameState
from src.core.game.EventHandlers import *
from src.core.game.querys import *
from src.features.characters.application.character_mapper import json_to_character


def build_game_state(campaign_code: str, campaigns, character_repository) -> GameState:
    dispatcher = EventDispatcher()

    campaign = campaigns.get(campaign_code)
    if not campaign:
        raise RuntimeError("Campaign not found")

    characters = {}

    for player in campaign["players"].values():
        char_id = player.get("character_uuid")
        if not char_id:
            continue

        data = character_repository.get_by_id(char_id)
        if not data:
            continue

        character = json_to_character(data)
        characters[character.id] = character

    state = GameState(
        characters=characters,
        current_turn=1,
        current_phase="exploration",
        dispatcher=dispatcher
    )

    # Registrar handlers
    dispatcher.register("attack_roll", StunnedAttackHandler())
    dispatcher.register("attack_hit", ApplyDamageHandler())
    dispatcher.register("status_requested", ApplyStatusHandler())
    dispatcher.register("attack_hit", RageDamageHandler())
    dispatcher.register("token_moved", TokenMovedHandler())
    dispatcher.register("create_enemy", CreateEnemyHandler())
    state.register_query_handler(GetArmorClass, GetArmorClassHandler())
    state.register_query_handler(GetStatModifier, GetStatModifierHandler())
    state.register_query_handler(GetEntities, GetEntitiesHandler())
    return state
