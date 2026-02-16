"""
Authentication utilities for session validation and user retrieval.
"""
from uuid import UUID
from typing import Optional, Tuple, Any
from flask import request, redirect
from dataclasses import dataclass


@dataclass
class AuthResult:
    """Result of authentication validation."""
    user: Optional[Any]
    session: Optional[Any]
    is_valid: bool
    redirect_response: Optional[Any] = None


def get_session_id_from_cookie() -> Optional[str]:
    """Extract session ID from cookie."""
    return request.cookies.get("session_id")


def validate_session_and_get_user(auth_service) -> AuthResult:
    """
    Validate session and retrieve user.
    
    Returns:
        AuthResult with user, session, and validity status
    """
    session_id = get_session_id_from_cookie()
    
    if not session_id:
        return AuthResult(
            user=None,
            session=None,
            is_valid=False,
            redirect_response=redirect("/login")
        )
    
    try:
        session = auth_service.session_repo.get(UUID(session_id))
    except (ValueError, Exception):
        return AuthResult(
            user=None,
            session=None,
            is_valid=False,
            redirect_response=redirect("/login")
        )
    
    if not session or session.revoked:
        return AuthResult(
            user=None,
            session=session,
            is_valid=False,
            redirect_response=redirect("/login")
        )
    
    user = auth_service.user_repo.get_by_id(session.user_id)
    
    if not user:
        return AuthResult(
            user=None,
            session=session,
            is_valid=False,
            redirect_response=redirect("/login")
        )
    
    return AuthResult(
        user=user,
        session=session,
        is_valid=True
    )


def require_authentication(auth_service):
    """
    Decorator/helper to require authentication.
    Returns (user, session) tuple or raises redirect.
    """
    auth_result = validate_session_and_get_user(auth_service)
    
    if not auth_result.is_valid:
        return None, auth_result.redirect_response
    
    return auth_result.user, None


def create_session_cookie(response, session_id: UUID):
    """
    Set session cookie on response object.
    
    Args:
        response: Flask response object
        session_id: Session UUID
    
    Returns:
        Modified response object
    """
    response.set_cookie(
        "session_id",
        str(session_id),
        httponly=True,
        samesite="Lax"
    )
    return response


def clear_session_cookie(response):
    """
    Clear session cookie from response.
    
    Args:
        response: Flask response object
    
    Returns:
        Modified response object
    """
    response.set_cookie("session_id", "", expires=0)
    return response


def login_user(auth_service, email: str, password: str) -> Tuple[Optional[Any], Optional[str]]:
    """
    Authenticate user and create session.
    
    Returns:
        Tuple of (session, error_message)
    """
    try:
        session = auth_service.login(email, password)
        return session, None
    except ValueError:
        return None, "Invalid credentials"


def register_and_login_user(
    auth_service,
    username: str,
    email: str,
    password: str
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Register new user and create session.
    
    Returns:
        Tuple of (session, error_message)
    """
    try:
        auth_service.register(username=username, email=email, password=password)
    except ValueError as e:
        return None, str(e)
    
    return login_user(auth_service, email, password)