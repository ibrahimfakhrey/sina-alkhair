from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from ..extensions import db
from ..models.case import Case
from ..models.finance_action import FinanceAction
from ..models.case_image import CaseImage
from ..utils.constants import UserRole, CaseStatus, FinanceStatus, ImageType
from ..utils.decorators import role_required, get_current_user
from ..utils.helpers import save_uploaded_file
from ..services import audit_service, notification_service

bp = Blueprint('finance', __name__, url_prefix='/api/finance')


@bp.route('/pending', methods=['GET'])
@jwt_required()
@role_required(UserRole.MANAGER_5)
def get_pending_payments():
    """Get cases pending payment"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Case.query.filter(
        Case.status == CaseStatus.PENDING_PAYMENT
    ).order_by(Case.updated_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'cases': [case.to_dict(include_details=True) for case in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@bp.route('/cases/<int:case_id>/confirm-ready', methods=['POST'])
@jwt_required()
@role_required(UserRole.MANAGER_5)
def confirm_ready_to_pay(case_id):
    """Confirm ready to pay"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    if case.status != CaseStatus.PENDING_PAYMENT:
        return jsonify({'error': 'Case is not pending payment'}), 400

    # Check if finance action exists
    finance_action = case.finance_action
    if not finance_action:
        finance_action = FinanceAction(
            case_id=case.id,
            finance_manager_id=current_user.id,
            status=FinanceStatus.READY_TO_PAY
        )
        db.session.add(finance_action)
    else:
        finance_action.status = FinanceStatus.READY_TO_PAY
        finance_action.finance_manager_id = current_user.id

    data = request.get_json() or {}
    if 'notes' in data:
        finance_action.notes = data['notes']

    db.session.commit()

    audit_service.log_payment_confirmed(case, current_user)
    notification_service.notify_payment_confirmed(case)

    return jsonify({
        'message': 'Payment confirmed as ready',
        'finance_action': finance_action.to_dict()
    }), 200


@bp.route('/cases/<int:case_id>/mark-paid', methods=['POST'])
@jwt_required()
@role_required(UserRole.MANAGER_5)
def mark_as_paid(case_id):
    """Mark case as paid and close it"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    if case.status != CaseStatus.PENDING_PAYMENT:
        return jsonify({'error': 'Case is not pending payment'}), 400

    # Get finance action
    finance_action = case.finance_action
    if not finance_action:
        finance_action = FinanceAction(
            case_id=case.id,
            finance_manager_id=current_user.id
        )
        db.session.add(finance_action)

    # Handle file upload for proof
    proof_path = None
    if request.content_type and 'multipart/form-data' in request.content_type:
        proof_file = request.files.get('proof')
        notes = request.form.get('notes')

        if proof_file:
            proof_path = save_uploaded_file(proof_file, ImageType.PAYMENT_PROOF)
            if not proof_path:
                return jsonify({'error': 'Invalid file type'}), 400

            # Also save as case image
            case_image = CaseImage(
                case_id=case.id,
                image_path=proof_path,
                image_type=ImageType.PAYMENT_PROOF,
                uploaded_by=current_user.id
            )
            db.session.add(case_image)
    else:
        data = request.get_json() or {}
        notes = data.get('notes')

    # Update finance action
    finance_action.status = FinanceStatus.PAID
    finance_action.finance_manager_id = current_user.id
    finance_action.paid_at = datetime.utcnow()
    finance_action.proof_image_path = proof_path
    if notes:
        finance_action.notes = notes

    # Close the case
    case.status = CaseStatus.CLOSED

    db.session.commit()

    audit_service.log_case_closed(case, current_user)
    notification_service.notify_case_closed(case)

    return jsonify({
        'message': 'Case marked as paid and closed',
        'case': case.to_dict(),
        'finance_action': finance_action.to_dict()
    }), 200


@bp.route('/history', methods=['GET'])
@jwt_required()
@role_required(UserRole.MANAGER_5, UserRole.OWNER)
def get_payment_history():
    """Get payment history"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = FinanceAction.query.filter(
        FinanceAction.status == FinanceStatus.PAID
    ).order_by(FinanceAction.paid_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'payments': [fa.to_dict() for fa in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200
