from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models.case import Case
from ..models.manager_approval import ManagerApproval
from ..models.user import User
from ..utils.constants import UserRole, CaseStatus, CaseType, ApprovalDecision
from ..utils.decorators import role_required, get_current_user
from ..services import approval_service, audit_service, notification_service

bp = Blueprint('approvals', __name__, url_prefix='/api/approvals')


@bp.route('/pending', methods=['GET'])
@jwt_required()
@role_required(UserRole.MANAGER_1, UserRole.MANAGER_2, UserRole.MANAGER_3, UserRole.MANAGER_4)
def get_pending_approvals():
    """Get cases pending current manager's approval"""
    current_user = get_current_user()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Get cases where this manager needs to approve
    if current_user.role == UserRole.MANAGER_3:
        # Manager 3 only approves donation cases
        query = Case.query.filter(
            Case.status == CaseStatus.PENDING_APPROVAL,
            Case.case_type == CaseType.DONATION
        )
    elif current_user.role == UserRole.MANAGER_4:
        # Manager 4 only approves medical cases
        query = Case.query.filter(
            Case.status == CaseStatus.PENDING_APPROVAL,
            Case.case_type == CaseType.MEDICAL
        )
    else:
        # Manager 1 and 2 approve all cases
        query = Case.query.filter(Case.status == CaseStatus.PENDING_APPROVAL)

    # Filter to cases where this manager hasn't approved yet
    subquery = ManagerApproval.query.filter(
        ManagerApproval.manager_role == current_user.role.value,
        ManagerApproval.decision == ApprovalDecision.APPROVED
    ).with_entities(ManagerApproval.case_id)

    query = query.filter(~Case.id.in_(subquery))
    query = query.order_by(Case.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'cases': [case.to_dict(include_details=True) for case in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@bp.route('/cases/<int:case_id>/status', methods=['GET'])
@jwt_required()
@role_required(UserRole.OWNER, UserRole.MANAGER_1, UserRole.MANAGER_2, UserRole.MANAGER_3, UserRole.MANAGER_4, UserRole.MANAGER_5)
def get_approval_status(case_id):
    """Get approval status for a case"""
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    status = approval_service.get_approval_status(case)

    return jsonify({
        'case_id': case_id,
        'case_number': case.case_number,
        'case_type': case.case_type.value,
        'case_status': case.status.value,
        'approvals': status
    }), 200


@bp.route('/cases/<int:case_id>/approve', methods=['POST'])
@jwt_required()
@role_required(UserRole.MANAGER_1, UserRole.MANAGER_2, UserRole.MANAGER_3, UserRole.MANAGER_4)
def approve_case(case_id):
    """Approve a case"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    # Check if manager can approve this case
    can_approve, error = approval_service.can_manager_approve(current_user, case)
    if not can_approve:
        return jsonify({'error': error}), 403

    data = request.get_json()
    amount = data.get('amount')

    if amount is None or amount <= 0:
        return jsonify({'error': 'Valid amount is required'}), 400

    # Get or create approval record
    approval = ManagerApproval.query.filter_by(
        case_id=case.id,
        manager_role=current_user.role.value
    ).first()

    if not approval:
        approval = ManagerApproval(
            case_id=case.id,
            manager_id=current_user.id,
            manager_role=current_user.role.value
        )
        db.session.add(approval)

    # Check if all other approvals have the same amount
    other_approvals = ManagerApproval.query.filter(
        ManagerApproval.case_id == case.id,
        ManagerApproval.manager_role != current_user.role.value,
        ManagerApproval.decision == ApprovalDecision.APPROVED
    ).all()

    for other in other_approvals:
        if other.amount_suggested != amount:
            return jsonify({
                'error': f'Amount must match other approvals. Expected: {other.amount_suggested}'
            }), 400

    approval.manager_id = current_user.id
    approval.decision = ApprovalDecision.APPROVED
    approval.amount_suggested = amount
    approval.rejection_reason = None
    approval.suggestion = None

    db.session.commit()

    # Log
    audit_service.log_case_approved(case, current_user, amount)

    # Check if all managers have approved
    if approval_service.check_all_approved(case):
        approval_service.finalize_approval(case)
        case.status = CaseStatus.PENDING_PAYMENT
        db.session.commit()
        notification_service.notify_case_approved(case)

    return jsonify({
        'message': 'Case approved successfully',
        'approval': approval.to_dict(),
        'all_approved': case.status == CaseStatus.PENDING_PAYMENT
    }), 200


@bp.route('/cases/<int:case_id>/reject', methods=['POST'])
@jwt_required()
@role_required(UserRole.MANAGER_1, UserRole.MANAGER_2, UserRole.MANAGER_3, UserRole.MANAGER_4)
def reject_case(case_id):
    """Reject a case"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    # Check if manager can approve/reject this case
    can_approve, error = approval_service.can_manager_approve(current_user, case)
    if not can_approve:
        return jsonify({'error': error}), 403

    data = request.get_json()
    reason = data.get('reason')
    suggestion = data.get('suggestion')

    if not reason:
        return jsonify({'error': 'Rejection reason is required'}), 400

    # Get or create approval record
    approval = ManagerApproval.query.filter_by(
        case_id=case.id,
        manager_role=current_user.role.value
    ).first()

    if not approval:
        approval = ManagerApproval(
            case_id=case.id,
            manager_id=current_user.id,
            manager_role=current_user.role.value
        )
        db.session.add(approval)

    approval.manager_id = current_user.id
    approval.decision = ApprovalDecision.REJECTED
    approval.rejection_reason = reason
    approval.suggestion = suggestion
    approval.amount_suggested = None

    # Reset all other approvals
    approval_service.reset_approvals(case)

    # Update case status
    case.status = CaseStatus.REJECTED

    db.session.commit()

    # Log and notify
    audit_service.log_case_rejected(case, current_user, reason, suggestion)

    # Notify managers 1 and 2 about rejection
    managers = User.query.filter(
        User.role.in_([UserRole.MANAGER_1, UserRole.MANAGER_2]),
        User.is_active == True
    ).all()
    notification_service.notify_case_rejected(case, [m.id for m in managers])

    return jsonify({
        'message': 'Case rejected',
        'approval': approval.to_dict()
    }), 200
