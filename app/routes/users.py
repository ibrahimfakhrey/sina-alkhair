from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..models.case import Case
from ..utils.constants import UserRole, CaseStatus
from ..utils.decorators import role_required, get_current_user
from ..utils.validators import validate_email, validate_username, validate_password

bp = Blueprint('users', __name__, url_prefix='/api/users')


@bp.route('', methods=['GET'])
@jwt_required()
@role_required(UserRole.OWNER, UserRole.MANAGER_1)
def list_users():
    """List all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    }), 200


@bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get user details"""
    current_user = get_current_user()

    # Check permissions
    if current_user.role not in [UserRole.OWNER, UserRole.MANAGER_1]:
        if current_user.id != user_id:
            return jsonify({'error': 'Insufficient permissions'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict(include_sensitive=True)}), 200


@bp.route('/researcher', methods=['POST'])
@jwt_required()
@role_required(UserRole.MANAGER_1)
def create_researcher():
    """Create a new researcher account"""
    current_user = get_current_user()
    data = request.get_json()

    # Validate required fields
    required_fields = ['username', 'email', 'password', 'full_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Validate username
    is_valid, error = validate_username(data['username'])
    if not is_valid:
        return jsonify({'error': error}), 400

    # Validate email
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400

    # Validate password
    is_valid, error = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': error}), 400

    # Check if username exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    # Check if email exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    researcher = User(
        username=data['username'],
        email=data['email'],
        full_name=data['full_name'],
        phone=data.get('phone'),
        role=UserRole.RESEARCHER,
        created_by=current_user.id
    )
    researcher.set_password(data['password'])

    db.session.add(researcher)
    db.session.commit()

    return jsonify({
        'message': 'Researcher created successfully',
        'user': researcher.to_dict()
    }), 201


@bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required(UserRole.MANAGER_1)
def update_user(user_id):
    """Update user details"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Manager 1 can only update researchers
    if user.role not in [UserRole.RESEARCHER]:
        return jsonify({'error': 'Can only update researcher accounts'}), 403

    data = request.get_json()

    if 'full_name' in data:
        user.full_name = data['full_name']

    if 'phone' in data:
        user.phone = data['phone']

    if 'email' in data:
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        if User.query.filter(User.email == data['email'], User.id != user_id).first():
            return jsonify({'error': 'Email already exists'}), 400
        user.email = data['email']

    if 'is_active' in data:
        user.is_active = data['is_active']

    db.session.commit()

    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@bp.route('/researchers', methods=['GET'])
@jwt_required()
@role_required(UserRole.MANAGER_1, UserRole.MANAGER_2)
def list_researchers():
    """List all researchers with their case load"""
    researchers = User.query.filter_by(role=UserRole.RESEARCHER, is_active=True).all()

    result = []
    for researcher in researchers:
        # Count active cases
        active_cases = Case.query.filter(
            Case.assigned_to == researcher.id,
            Case.status.in_([
                CaseStatus.ASSIGNED,
                CaseStatus.INVESTIGATING
            ])
        ).count()

        # Count total cases
        total_cases = Case.query.filter_by(assigned_to=researcher.id).count()

        researcher_data = researcher.to_dict()
        researcher_data['active_cases'] = active_cases
        researcher_data['total_cases'] = total_cases
        result.append(researcher_data)

    return jsonify({'researchers': result}), 200
