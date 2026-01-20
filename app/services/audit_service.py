from ..extensions import db
from ..models.audit_log import AuditLog
from ..utils.constants import AuditAction


def log_action(case_id, user_id, action, details=None):
    """Create an audit log entry"""
    audit_log = AuditLog(
        case_id=case_id,
        user_id=user_id,
        action=action
    )
    if details:
        audit_log.set_details(details)

    db.session.add(audit_log)
    db.session.commit()
    return audit_log


def log_case_created(case, user):
    """Log case creation"""
    return log_action(
        case_id=case.id,
        user_id=user.id,
        action=AuditAction.CASE_CREATED,
        details={
            'case_number': case.case_number,
            'case_type': case.case_type.value,
            'created_by': user.full_name
        }
    )


def log_case_updated(case, user, changes):
    """Log case update"""
    return log_action(
        case_id=case.id,
        user_id=user.id,
        action=AuditAction.CASE_UPDATED,
        details={
            'changes': changes,
            'updated_by': user.full_name
        }
    )


def log_case_assigned(case, user, researcher):
    """Log case assignment"""
    return log_action(
        case_id=case.id,
        user_id=user.id,
        action=AuditAction.CASE_ASSIGNED,
        details={
            'assigned_to': researcher.full_name,
            'assigned_by': user.full_name
        }
    )


def log_case_reassigned(case, user, old_researcher, new_researcher):
    """Log case reassignment"""
    return log_action(
        case_id=case.id,
        user_id=user.id,
        action=AuditAction.CASE_REASSIGNED,
        details={
            'from_researcher': old_researcher.full_name if old_researcher else None,
            'to_researcher': new_researcher.full_name,
            'reassigned_by': user.full_name
        }
    )


def log_investigation_submitted(case, researcher):
    """Log investigation submission"""
    return log_action(
        case_id=case.id,
        user_id=researcher.id,
        action=AuditAction.INVESTIGATION_SUBMITTED,
        details={
            'researcher': researcher.full_name,
            'recommendation': case.report.recommendation.value if case.report and case.report.recommendation else None
        }
    )


def log_investigation_updated(case, researcher):
    """Log investigation update"""
    return log_action(
        case_id=case.id,
        user_id=researcher.id,
        action=AuditAction.INVESTIGATION_UPDATED,
        details={
            'researcher': researcher.full_name
        }
    )


def log_case_approved(case, manager, amount):
    """Log case approval"""
    return log_action(
        case_id=case.id,
        user_id=manager.id,
        action=AuditAction.CASE_APPROVED,
        details={
            'manager': manager.full_name,
            'manager_role': manager.role.value,
            'amount': amount
        }
    )


def log_case_rejected(case, manager, reason, suggestion):
    """Log case rejection"""
    return log_action(
        case_id=case.id,
        user_id=manager.id,
        action=AuditAction.CASE_REJECTED,
        details={
            'manager': manager.full_name,
            'manager_role': manager.role.value,
            'reason': reason,
            'suggestion': suggestion
        }
    )


def log_payment_confirmed(case, finance_manager):
    """Log payment confirmation"""
    return log_action(
        case_id=case.id,
        user_id=finance_manager.id,
        action=AuditAction.PAYMENT_CONFIRMED,
        details={
            'finance_manager': finance_manager.full_name,
            'amount': case.amount_approved
        }
    )


def log_case_closed(case, user):
    """Log case closure"""
    return log_action(
        case_id=case.id,
        user_id=user.id,
        action=AuditAction.CASE_CLOSED,
        details={
            'closed_by': user.full_name,
            'final_amount': case.amount_approved
        }
    )


def log_image_uploaded(case, user, image_type):
    """Log image upload"""
    return log_action(
        case_id=case.id,
        user_id=user.id,
        action=AuditAction.IMAGE_UPLOADED,
        details={
            'uploaded_by': user.full_name,
            'image_type': image_type
        }
    )


def log_image_deleted(case, user, image_id):
    """Log image deletion"""
    return log_action(
        case_id=case.id,
        user_id=user.id,
        action=AuditAction.IMAGE_DELETED,
        details={
            'deleted_by': user.full_name,
            'image_id': image_id
        }
    )
