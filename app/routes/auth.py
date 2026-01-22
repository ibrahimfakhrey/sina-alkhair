from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from ..extensions import db
from ..models.user import User
from ..utils.constants import UserRole
from ..utils.validators import validate_password
from ..utils.decorators import get_current_user as get_user

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Store for revoked tokens (in production, use Redis)
revoked_tokens = set()


@bp.route('/login', methods=['POST'])
def login():
    """Login with username and password"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout - revoke current token and clear FCM token"""
    jti = get_jwt()['jti']
    revoked_tokens.add(jti)

    # Clear FCM token on logout
    current_user = get_user()
    if current_user:
        current_user.fcm_token = None
        current_user.fcm_platform = None
        db.session.commit()

    return jsonify({'message': 'Successfully logged out'}), 200


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user or not user.is_active:
        return jsonify({'error': 'Invalid user'}), 401

    access_token = create_access_token(identity=str(user_id))
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change own password"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({'error': 'Old password and new password are required'}), 400

    if not user.check_password(old_password):
        return jsonify({'error': 'Current password is incorrect'}), 400

    # Validate new password
    is_valid, error = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': error}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Password changed successfully'}), 200


@bp.route('/reset-password/<int:user_id>', methods=['POST'])
@jwt_required()
def reset_password(user_id):
    """Reset another user's password (Manager 1 only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(int(current_user_id))

    if not current_user or current_user.role != UserRole.MANAGER_1:
        return jsonify({'error': 'Only Manager 1 can reset passwords'}), 403

    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    # Cannot reset owner's password
    if target_user.role == UserRole.OWNER:
        return jsonify({'error': 'Cannot reset owner password'}), 403

    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({'error': 'New password is required'}), 400

    is_valid, error = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': error}), 400

    target_user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': f'Password reset successfully for {target_user.username}'}), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()}), 200
