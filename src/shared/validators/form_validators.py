"""
Form validation utilities.
"""
from typing import Tuple, Optional


def validate_login_form(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate login form data.
    
    Args:
        email: Email address
        password: Password
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not password:
        return False, "Email and password are required"
    
    return True, None


def validate_registration_form(
    username: str,
    email: str,
    password: str,
    confirm_password: str,
    terms: bool
) -> Tuple[bool, Optional[str]]:
    """
    Validate registration form data.
    
    Args:
        username: Username
        email: Email address
        password: Password
        confirm_password: Password confirmation
        terms: Terms acceptance
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not email or not password or not confirm_password:
        return False, "Todos los campos son obligatorios"
    
    if password != confirm_password:
        return False, "Las contraseñas no coinciden"
    
    if not terms:
        return False, "Debes aceptar los términos"
    
    return True, None