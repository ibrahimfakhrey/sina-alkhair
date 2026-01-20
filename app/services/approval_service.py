from ..extensions import db
from ..models.manager_approval import ManagerApproval
from ..models.case import Case
from ..utils.constants import (
    CaseType, CaseStatus, ApprovalDecision, UserRole,
    REQUIRED_MANAGERS_DONATION, REQUIRED_MANAGERS_MEDICAL
)


def get_required_managers(case_type):
    """Get list of required manager roles for case type"""
    if case_type == CaseType.DONATION:
        return REQUIRED_MANAGERS_DONATION
    else:
        return REQUIRED_MANAGERS_MEDICAL


def create_approval_records(case):
    """Create pending approval records for all required managers"""
    required_roles = get_required_managers(case.case_type)

    for role in required_roles:
        existing = ManagerApproval.query.filter_by(
            case_id=case.id,
            manager_role=role.value
        ).first()

        if not existing:
            approval = ManagerApproval(
                case_id=case.id,
                manager_id=None,  # Will be set when manager approves
                manager_role=role.value,
                decision=ApprovalDecision.PENDING
            )
            db.session.add(approval)

    db.session.commit()


def reset_approvals(case):
    """Reset all approvals to pending (when one manager rejects)"""
    approvals = ManagerApproval.query.filter_by(case_id=case.id).all()

    for approval in approvals:
        approval.decision = ApprovalDecision.PENDING
        approval.amount_suggested = None
        approval.rejection_reason = None
        approval.suggestion = None

    case.status = CaseStatus.PENDING_APPROVAL
    db.session.commit()


def can_manager_approve(user, case):
    """Check if a manager can approve this case"""
    required_roles = get_required_managers(case.case_type)

    # Check if user's role is in required managers
    if user.role not in required_roles:
        return False, 'ليس لديك صلاحية الموافقة على هذه الحالة'

    # Check if case is in pending_approval status
    if case.status != CaseStatus.PENDING_APPROVAL:
        return False, 'الحالة ليست في مرحلة انتظار الموافقة'

    return True, None


def check_all_approved(case):
    """Check if all required managers have approved"""
    required_roles = get_required_managers(case.case_type)

    for role in required_roles:
        approval = ManagerApproval.query.filter_by(
            case_id=case.id,
            manager_role=role.value
        ).first()

        if not approval or approval.decision != ApprovalDecision.APPROVED:
            return False

    return True


def get_approval_status(case):
    """Get detailed approval status for a case"""
    required_roles = get_required_managers(case.case_type)
    status = []

    for role in required_roles:
        approval = ManagerApproval.query.filter_by(
            case_id=case.id,
            manager_role=role.value
        ).first()

        status.append({
            'role': role.value,
            'decision': approval.decision.value if approval else 'pending',
            'amount': approval.amount_suggested if approval else None,
            'manager_name': approval.manager.full_name if approval and approval.manager else None
        })

    return status


def finalize_approval(case):
    """Finalize case approval - set amount and status"""
    approvals = ManagerApproval.query.filter_by(
        case_id=case.id,
        decision=ApprovalDecision.APPROVED
    ).all()

    if not approvals:
        return False

    # All managers should agree on the same amount
    # Use the first approval's amount (they should all be the same)
    amount = approvals[0].amount_suggested

    case.amount_approved = amount
    case.status = CaseStatus.APPROVED
    db.session.commit()

    return True
