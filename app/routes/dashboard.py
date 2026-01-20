from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from ..extensions import db
from ..models.case import Case
from ..models.user import User
from ..models.finance_action import FinanceAction
from ..utils.constants import UserRole, CaseStatus, CaseType, FinanceStatus
from ..utils.decorators import role_required

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@bp.route('/statistics', methods=['GET'])
@jwt_required()
@role_required(UserRole.OWNER)
def get_statistics():
    """Get full dashboard statistics"""
    # Total cases
    total_cases = Case.query.count()

    # Cases by status
    cases_by_status = {}
    for status in CaseStatus:
        count = Case.query.filter_by(status=status).count()
        cases_by_status[status.value] = count

    # Cases by type
    cases_by_type = {}
    for case_type in CaseType:
        count = Case.query.filter_by(case_type=case_type).count()
        cases_by_type[case_type.value] = count

    # Total money spent
    total_spent = db.session.query(
        func.sum(Case.amount_approved)
    ).filter(Case.status == CaseStatus.CLOSED).scalar() or 0

    # Cases this month
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    cases_this_month = Case.query.filter(
        Case.created_at >= first_day_of_month
    ).count()

    # Closed this month
    closed_this_month = Case.query.filter(
        Case.status == CaseStatus.CLOSED,
        Case.updated_at >= first_day_of_month
    ).count()

    # Money spent this month
    spent_this_month = db.session.query(
        func.sum(Case.amount_approved)
    ).filter(
        Case.status == CaseStatus.CLOSED,
        Case.updated_at >= first_day_of_month
    ).scalar() or 0

    # Active researchers
    active_researchers = User.query.filter_by(
        role=UserRole.RESEARCHER,
        is_active=True
    ).count()

    # Pending cases (needs action)
    pending_approval = Case.query.filter_by(status=CaseStatus.PENDING_APPROVAL).count()
    pending_payment = Case.query.filter_by(status=CaseStatus.PENDING_PAYMENT).count()
    pending_assignment = Case.query.filter(
        Case.status.in_([CaseStatus.NEW, CaseStatus.PENDING_DATA]),
        Case.assigned_to.is_(None)
    ).count()

    return jsonify({
        'total_cases': total_cases,
        'cases_by_status': cases_by_status,
        'cases_by_type': cases_by_type,
        'total_spent': total_spent,
        'this_month': {
            'new_cases': cases_this_month,
            'closed_cases': closed_this_month,
            'spent': spent_this_month
        },
        'active_researchers': active_researchers,
        'pending': {
            'needs_assignment': pending_assignment,
            'needs_approval': pending_approval,
            'needs_payment': pending_payment
        }
    }), 200


@bp.route('/cases-summary', methods=['GET'])
@jwt_required()
@role_required(UserRole.OWNER)
def get_cases_summary():
    """Get cases summary by status"""
    summary = []

    for status in CaseStatus:
        cases = Case.query.filter_by(status=status).order_by(Case.created_at.desc()).limit(5).all()
        summary.append({
            'status': status.value,
            'count': Case.query.filter_by(status=status).count(),
            'recent_cases': [c.to_dict() for c in cases]
        })

    return jsonify({'summary': summary}), 200


@bp.route('/monthly-spending', methods=['GET'])
@jwt_required()
@role_required(UserRole.OWNER)
def get_monthly_spending():
    """Get money spent per month (last 12 months)"""
    current_year = datetime.now().year
    current_month = datetime.now().month

    spending = []

    for i in range(12):
        month = current_month - i
        year = current_year

        if month <= 0:
            month += 12
            year -= 1

        # Get total spent in this month
        total = db.session.query(
            func.sum(Case.amount_approved)
        ).filter(
            Case.status == CaseStatus.CLOSED,
            extract('year', Case.updated_at) == year,
            extract('month', Case.updated_at) == month
        ).scalar() or 0

        # Get count of closed cases
        count = Case.query.filter(
            Case.status == CaseStatus.CLOSED,
            extract('year', Case.updated_at) == year,
            extract('month', Case.updated_at) == month
        ).count()

        spending.append({
            'year': year,
            'month': month,
            'total_spent': total,
            'cases_closed': count
        })

    return jsonify({'monthly_spending': list(reversed(spending))}), 200


@bp.route('/researchers-performance', methods=['GET'])
@jwt_required()
@role_required(UserRole.OWNER)
def get_researchers_performance():
    """Get researcher performance statistics"""
    researchers = User.query.filter_by(role=UserRole.RESEARCHER, is_active=True).all()

    performance = []

    for researcher in researchers:
        # Total assigned cases
        total_assigned = Case.query.filter_by(assigned_to=researcher.id).count()

        # Active cases
        active_cases = Case.query.filter(
            Case.assigned_to == researcher.id,
            Case.status.in_([CaseStatus.ASSIGNED, CaseStatus.INVESTIGATING])
        ).count()

        # Completed investigations
        completed = Case.query.filter(
            Case.assigned_to == researcher.id,
            Case.status.in_([
                CaseStatus.PENDING_APPROVAL,
                CaseStatus.APPROVED,
                CaseStatus.PENDING_PAYMENT,
                CaseStatus.CLOSED
            ])
        ).count()

        performance.append({
            'researcher': researcher.to_dict(),
            'total_assigned': total_assigned,
            'active_cases': active_cases,
            'completed_investigations': completed
        })

    return jsonify({'researchers_performance': performance}), 200


@bp.route('/recent-activity', methods=['GET'])
@jwt_required()
@role_required(UserRole.OWNER)
def get_recent_activity():
    """Get recent case activity"""
    from ..models.audit_log import AuditLog

    recent_logs = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).limit(50).all()

    return jsonify({
        'recent_activity': [log.to_dict() for log in recent_logs]
    }), 200
