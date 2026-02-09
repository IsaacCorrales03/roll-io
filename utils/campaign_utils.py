"""
Campaign and lobby management utilities.
"""
from typing import Optional, Dict, Any
from utils.gen_code import generate_campaign_code


def validate_lobby(code: str, campaigns: Dict[str, Any]) -> bool:
    """
    Check if lobby exists.
    
    Args:
        code: Lobby code
        campaigns: Dictionary of active campaigns
    
    Returns:
        True if lobby exists, False otherwise
    """
    return code in campaigns


def get_campaign_id_from_lobby(code: str, campaigns: Dict[str, Any]) -> Optional[str]:
    """
    Get campaign ID from lobby code.
    
    Args:
        code: Lobby code
        campaigns: Dictionary of active campaigns
    
    Returns:
        Campaign ID or None if not found
    """
    lobby = campaigns.get(code)
    return lobby["campaign_id"] if lobby else None


def get_or_create_lobby(campaign_id: str, campaigns: Dict[str, Any]) -> str:
    """
    Get existing lobby code or create new one for campaign.
    
    Args:
        campaign_id: Campaign identifier
        campaigns: Dictionary of active campaigns
    
    Returns:
        Lobby code
    """
    # Check if lobby already exists
    for code, lobby in campaigns.items():
        if lobby["campaign_id"] == campaign_id:
            return code
    
    # Create new lobby
    code = generate_campaign_code()
    campaigns[code] = {
        "campaign_id": campaign_id,
        "players": {}
    }
    return code


def is_user_dm(campaign, user_id: str) -> bool:
    """
    Check if user is the DM of the campaign.
    
    Args:
        campaign: Campaign object
        user_id: User identifier
    
    Returns:
        True if user is DM, False otherwise
    """
    return campaign and str(campaign.owner_id) == user_id


def get_players_not_ready(players: list) -> list:
    """
    Get list of players who haven't selected a character.
    
    Args:
        players: List of player dictionaries
    
    Returns:
        List of players not ready
    """
    return [
        p for p in players
        if not p["is_dm"] and not p.get("character_uuid")
    ]


def find_player_by_sid(players: Dict[str, Any], sid: str) -> Optional[Dict[str, Any]]:
    """
    Find player by socket ID.
    
    Args:
        players: Dictionary of players
        sid: Socket ID
    
    Returns:
        Player dictionary or None
    """
    for player in players.values():
        if player.get("sid") == sid:
            return player
    return None


def create_player_data(
    user_id: str,
    username: str,
    sid: str,
    is_dm: bool,
    character_uuid: Optional[str] = None,
    character_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create player data dictionary.
    
    Args:
        user_id: User identifier
        username: Username
        sid: Socket ID
        is_dm: Whether user is DM
        character_uuid: Optional character UUID
        character_name: Optional character name
    
    Returns:
        Player data dictionary
    """
    return {
        "user_id": user_id,
        "username": username,
        "character_uuid": character_uuid,
        "character_name": character_name,
        "sid": sid,
        "is_dm": is_dm
    }