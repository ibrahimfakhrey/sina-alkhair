from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models.case import Case
from ..models.user import User
from ..utils.constants import UserRole, CaseType, CaseStatus
from ..utils.decorators import role_required, get_current_user
from ..utils.helpers import save_uploaded_file
from ..utils.constants import ImageType
from ..services import case_service, audit_service, notification_service

bp = Blueprint('cases', __name__, url_prefix='/api/cases')


@bp.route('', methods=['GET'])
@jwt_required()
def list_cases():
    """List cases (filtered by role)"""
    current_user = get_current_user()

    # Get query parameters for filtering
    status = request.args.get('status')
    case_type = request.args.get('type')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = case_service.get_cases_for_user(current_user)

    # Apply filters
    if status:
        try:
            query = query.filter(Case.status == CaseStatus(status))
        except ValueError:
            pass

    if case_type:
        try:
            query = query.filter(Case.case_type == CaseType(case_type))
        except ValueError:
            pass

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'cases': [case.to_dict() for case in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@bp.route('/<int:case_id>', methods=['GET'])
@jwt_required()
def get_case(case_id):
    """Get case with full details"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    # Researchers can only view their assigned cases
    if current_user.role == UserRole.RESEARCHER and case.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({'case': case.to_dict(include_details=True)}), 200


@bp.route('', methods=['POST'])
@jwt_required()
@role_required(UserRole.OWNER, UserRole.MANAGER_1, UserRole.MANAGER_2)
def create_case():
    """Create a new case"""
    current_user = get_current_user()

    # Handle form data (with file) or JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        case_type = request.form.get('case_type')
        screenshot = request.files.get('screenshot')

        beneficiary_data = {
            'name': request.form.get('name'),
            'phone': request.form.get('phone'),
            'id_number': request.form.get('id_number'),
            'address': request.form.get('address')
        }
    else:
        data = request.get_json() or {}
        case_type = data.get('case_type')
        screenshot = None
        beneficiary_data = {
            'name': data.get('name'),
            'phone': data.get('phone'),
            'id_number': data.get('id_number'),
            'address': data.get('address')
        }

    if not case_type:
        return jsonify({'error': 'case_type is required (medical or donation)'}), 400

    try:
        case_type_enum = CaseType(case_type)
    except ValueError:
        return jsonify({'error': 'Invalid case_type. Must be "medical" or "donation"'}), 400

    # Owner must upload screenshot, managers can create without
    screenshot_path = None
    if current_user.role == UserRole.OWNER:
        if not screenshot:
            return jsonify({'error': 'Screenshot is required for owner'}), 400
        screenshot_path = save_uploaded_file(screenshot, ImageType.SCREENSHOT)
        if not screenshot_path:
            return jsonify({'error': 'Invalid file type or file too large'}), 400

    elif screenshot:
        screenshot_path = save_uploaded_file(screenshot, ImageType.SCREENSHOT)

    # Create the case
    case = case_service.create_case(
        case_type=case_type_enum,
        created_by=current_user.id,
        screenshot_path=screenshot_path,
        beneficiary_data=beneficiary_data
    )

    # Log and notify
    audit_service.log_case_created(case, current_user)
    notification_service.notify_case_created(case)

    return jsonify({
        'message': 'Case created successfully',
        'case': case.to_dict()
    }), 201


@bp.route('/<int:case_id>', methods=['PUT'])
@jwt_required()
@role_required(UserRole.MANAGER_1, UserRole.MANAGER_2)
def update_case(case_id):
    """Update case data"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    # Can only update cases that are not closed
    if case.status == CaseStatus.CLOSED:
        return jsonify({'error': 'Cannot update closed case'}), 400

    data = request.get_json()

    changes = case_service.update_case(case, data)

    if changes:
        audit_service.log_case_updated(case, current_user, changes)

    return jsonify({
        'message': 'Case updated successfully',
        'case': case.to_dict()
    }), 200


@bp.route('/<int:case_id>/assign', methods=['POST'])
@jwt_required()
@role_required(UserRole.MANAGER_1, UserRole.MANAGER_2)
def assign_case(case_id):
    """Assign case to a researcher"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    if case.assigned_to:
        return jsonify({'error': 'Case already assigned. Use reassign endpoint'}), 400

    data = request.get_json()
    researcher_id = data.get('researcher_id')

    if not researcher_id:
        return jsonify({'error': 'researcher_id is required'}), 400

    researcher = User.query.get(researcher_id)
    if not researcher or researcher.role != UserRole.RESEARCHER:
        return jsonify({'error': 'Invalid researcher'}), 400

    if not researcher.is_active:
        return jsonify({'error': 'Researcher account is deactivated'}), 400

    case_service.assign_case(case, researcher_id)

    audit_service.log_case_assigned(case, current_user, researcher)
    notification_service.notify_case_assigned(case, researcher)

    return jsonify({
        'message': 'Case assigned successfully',
        'case': case.to_dict()
    }), 200


@bp.route('/<int:case_id>/reassign', methods=['POST'])
@jwt_required()
@role_required(UserRole.MANAGER_1, UserRole.MANAGER_2)
def reassign_case(case_id):
    """Reassign case to a different researcher"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    if not case.assigned_to:
        return jsonify({'error': 'Case not assigned yet. Use assign endpoint'}), 400

    data = request.get_json()
    new_researcher_id = data.get('researcher_id')

    if not new_researcher_id:
        return jsonify({'error': 'researcher_id is required'}), 400

    if new_researcher_id == case.assigned_to:
        return jsonify({'error': 'Case already assigned to this researcher'}), 400

    new_researcher = User.query.get(new_researcher_id)
    if not new_researcher or new_researcher.role != UserRole.RESEARCHER:
        return jsonify({'error': 'Invalid researcher'}), 400

    if not new_researcher.is_active:
        return jsonify({'error': 'Researcher account is deactivated'}), 400

    old_researcher = User.query.get(case.assigned_to)
    case_service.reassign_case(case, new_researcher_id)

    audit_service.log_case_reassigned(case, current_user, old_researcher, new_researcher)
    notification_service.notify_case_reassigned(case, old_researcher, new_researcher)

    return jsonify({
        'message': 'Case reassigned successfully',
        'case': case.to_dict()
    }), 200


@bp.route('/search', methods=['GET'])
@jwt_required()
@role_required(UserRole.OWNER, UserRole.MANAGER_1, UserRole.MANAGER_2, UserRole.MANAGER_3, UserRole.MANAGER_4, UserRole.MANAGER_5)
def search_cases():
    """Search cases by various fields"""
    current_user = get_current_user()
    query = request.args.get('q', '')

    if not query or len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    results = case_service.search_cases(query, current_user)
    pagination = results.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'cases': [case.to_dict() for case in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'query': query
    }), 200
