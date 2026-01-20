from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models.case import Case
from ..models.researcher_report import ResearcherReport
from ..models.case_image import CaseImage
from ..utils.constants import UserRole, CaseStatus, Recommendation, ImageType
from ..utils.decorators import role_required, get_current_user
from ..utils.helpers import save_uploaded_file
from ..services import case_service, audit_service, notification_service, approval_service

bp = Blueprint('research', __name__, url_prefix='/api/research')


@bp.route('/my-cases', methods=['GET'])
@jwt_required()
@role_required(UserRole.RESEARCHER)
def get_my_cases():
    """Get cases assigned to current researcher"""
    current_user = get_current_user()

    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Case.query.filter_by(assigned_to=current_user.id)

    if status:
        try:
            query = query.filter(Case.status == CaseStatus(status))
        except ValueError:
            pass

    query = query.order_by(Case.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'cases': [case.to_dict() for case in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@bp.route('/cases/<int:case_id>/investigation', methods=['POST'])
@jwt_required()
@role_required(UserRole.RESEARCHER)
def submit_investigation(case_id):
    """Submit investigation report"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    if case.assigned_to != current_user.id:
        return jsonify({'error': 'This case is not assigned to you'}), 403

    if case.status not in [CaseStatus.ASSIGNED, CaseStatus.INVESTIGATING]:
        return jsonify({'error': 'Cannot submit investigation for this case status'}), 400

    # Check if report already exists
    if case.report:
        return jsonify({'error': 'Investigation already submitted. Use PUT to update'}), 400

    # Get form data
    if request.content_type and 'multipart/form-data' in request.content_type:
        verified_name = request.form.get('verified_name')
        verified_phone = request.form.get('verified_phone')
        verified_id_number = request.form.get('verified_id_number')
        verified_address = request.form.get('verified_address')
        opinion = request.form.get('opinion')
        recommendation = request.form.get('recommendation')
        images_count = request.form.get('images_count', 0, type=int)
    else:
        data = request.get_json() or {}
        verified_name = data.get('verified_name')
        verified_phone = data.get('verified_phone')
        verified_id_number = data.get('verified_id_number')
        verified_address = data.get('verified_address')
        opinion = data.get('opinion')
        recommendation = data.get('recommendation')
        images_count = data.get('images_count', 0)

    # Validate recommendation
    recommendation_enum = None
    if recommendation:
        try:
            recommendation_enum = Recommendation(recommendation)
        except ValueError:
            return jsonify({'error': 'Invalid recommendation. Must be "deserves" or "not_deserves"'}), 400

    # Create report
    report = ResearcherReport(
        case_id=case.id,
        researcher_id=current_user.id,
        verified_name=verified_name,
        verified_phone=verified_phone,
        verified_id_number=verified_id_number,
        verified_address=verified_address,
        opinion=opinion,
        recommendation=recommendation_enum,
        images_count=images_count
    )

    db.session.add(report)

    # Handle image uploads
    if request.content_type and 'multipart/form-data' in request.content_type:
        for i in range(images_count):
            image_file = request.files.get(f'image_{i}')
            if image_file:
                image_path = save_uploaded_file(image_file, ImageType.INVESTIGATION)
                if image_path:
                    case_image = CaseImage(
                        case_id=case.id,
                        image_path=image_path,
                        image_type=ImageType.INVESTIGATION,
                        uploaded_by=current_user.id
                    )
                    db.session.add(case_image)

    # Update case status
    case.status = CaseStatus.PENDING_APPROVAL

    # Create approval records for required managers
    approval_service.create_approval_records(case)

    db.session.commit()

    # Log and notify
    audit_service.log_investigation_submitted(case, current_user)
    notification_service.notify_investigation_submitted(case)

    return jsonify({
        'message': 'Investigation submitted successfully',
        'report': report.to_dict()
    }), 201


@bp.route('/cases/<int:case_id>/investigation', methods=['PUT'])
@jwt_required()
@role_required(UserRole.RESEARCHER)
def update_investigation(case_id):
    """Update investigation report"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    if case.assigned_to != current_user.id:
        return jsonify({'error': 'This case is not assigned to you'}), 403

    if not case.report:
        return jsonify({'error': 'No investigation report found. Use POST to create'}), 404

    # Only allow update in certain statuses
    if case.status not in [CaseStatus.INVESTIGATING, CaseStatus.PENDING_APPROVAL]:
        return jsonify({'error': 'Cannot update investigation for this case status'}), 400

    data = request.get_json() or {}
    report = case.report

    if 'verified_name' in data:
        report.verified_name = data['verified_name']
    if 'verified_phone' in data:
        report.verified_phone = data['verified_phone']
    if 'verified_id_number' in data:
        report.verified_id_number = data['verified_id_number']
    if 'verified_address' in data:
        report.verified_address = data['verified_address']
    if 'opinion' in data:
        report.opinion = data['opinion']
    if 'recommendation' in data:
        try:
            report.recommendation = Recommendation(data['recommendation'])
        except ValueError:
            return jsonify({'error': 'Invalid recommendation'}), 400

    db.session.commit()

    audit_service.log_investigation_updated(case, current_user)

    return jsonify({
        'message': 'Investigation updated successfully',
        'report': report.to_dict()
    }), 200
