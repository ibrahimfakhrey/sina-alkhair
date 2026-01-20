from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from ..models.user import User
from .constants import UserRole


def role_required(*roles):
    """Decorator to check if current user has required role"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))

            if not user:
                return jsonify({'error': 'User not found'}), 404

            if not user.is_active:
                return jsonify({'error': 'Account is deactivated'}), 403

            if user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def owner_only(fn):
    """Decorator for owner-only endpoints"""
    return role_required(UserRole.OWNER)(fn)


def manager_only(fn):
    """Decorator for any manager"""
    return role_required(
        UserRole.MANAGER_1,
        UserRole.MANAGER_2,
        UserRole.MANAGER_3,
        UserRole.MANAGER_4,
        UserRole.MANAGER_5
    )(fn)


def manager_1_only(fn):
    """Decorator for manager 1 only"""
    return role_required(UserRole.MANAGER_1)(fn)


def manager_1_2_only(fn):
    """Decorator for manager 1 or 2"""
    return role_required(UserRole.MANAGER_1, UserRole.MANAGER_2)(fn)


def researcher_only(fn):
    """Decorator for researcher only"""
    return role_required(UserRole.RESEARCHER)(fn)


def finance_only(fn):
    """Decorator for finance manager only"""
    return role_required(UserRole.MANAGER_5)(fn)


def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))
