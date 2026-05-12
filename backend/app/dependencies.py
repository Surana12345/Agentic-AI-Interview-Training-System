"""
Shared authentication dependencies.
Import get_current_user from here in any route file that needs JWT protection.
"""
from app.api.routes_auth import get_current_user

__all__ = ["get_current_user"]
