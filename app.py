"""
Main Application Entry Point
Integrates HTTP routes and WebSocket handlers
"""

import time
from flask_socketio import SocketIO

# HTTP routes
from http_app import create_app

# Socket handlers
from socket_app import register_socket_handlers

# Services
from services.auth_service import AuthService
from services.db_service import create_db_service
from auth.infrastructure.user_repository import MySQLUserRepository
from auth.infrastructure.auth_session_repository import MySQLAuthSessionRepository
from auth.infrastructure.bcrypt_hasher import BcryptPasswordHasher
from campaigns.infrastructure.mysql_campaign_repository import MySQLCampaignRepository
from services.character_repository import CharacterRepository


# ==========================
# Shared State
# ==========================
connected_clients = {}
campaigns = {}
worlds = {}
socket_campaigns: dict[str, str] = {}
game_states = {}


def main():
    """Initialize and run the application"""
    __START_TIME__ = time.perf_counter()

    # Create Flask app with shared state
    app = create_app(
        campaigns_dict=campaigns,
        worlds_dict=worlds,
        game_states_dict=game_states
    )

    # Initialize SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        ping_timeout=60,
        ping_interval=25,
        manage_session=False
    )

    # Initialize services for socket handlers
    db = create_db_service()
    user_repo = MySQLUserRepository(db)
    session_repo = MySQLAuthSessionRepository(db)
    password_hasher = BcryptPasswordHasher()
    auth_service = AuthService(user_repo, session_repo, password_hasher)
    campaign_repo = MySQLCampaignRepository(db)
    character_repo = CharacterRepository()

    # Register WebSocket handlers
    register_socket_handlers(
        socketio=socketio,
        campaigns_dict=campaigns,
        game_states_dict=game_states,
        connected_clients_dict=connected_clients,
        socket_campaigns_dict=socket_campaigns,
        auth_service=auth_service,
        campaign_repo=campaign_repo,
        character_repo=character_repo
    )

    # Print startup time
    startup_time = time.perf_counter() - __START_TIME__
    print(f"[BOOT] Startup time: {startup_time:.3f}s")

    # Run the application
    socketio.run(
        app=app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )


if __name__ == '__main__':
    main()