from datetime import datetime
from ..extensions import db
from ..models.case import Case
from ..utils.constants import CaseType, CaseStatus
from ..utils.helpers import generate_case_number


def create_case(case_type, created_by, screenshot_path=None, beneficiary_data=None):
    """Create a new case"""
    case_number = generate_case_number(case_type, db)

    case = Case(
        case_number=case_number,
        case_type=case_type,
        status=CaseStatus.NEW if screenshot_path else CaseStatus.PENDING_DATA,
        initial_screenshot=screenshot_path,
        created_by=created_by
    )

    # Fill beneficiary data if provided
    if beneficiary_data:
        case.beneficiary_name = beneficiary_data.get('name')
        case.beneficiary_phone = beneficiary_data.get('phone')
        case.beneficiary_id_number = beneficiary_data.get('id_number')
        case.beneficiary_address = beneficiary_data.get('address')
        if any([case.beneficiary_name, case.beneficiary_phone,
                case.beneficiary_id_number, case.beneficiary_address]):
            case.status = CaseStatus.PENDING_DATA

    db.session.add(case)
    db.session.commit()

    return case


def update_case(case, data):
    """Update case data"""
    changes = {}

    if 'name' in data and data['name'] != case.beneficiary_name:
        changes['name'] = {'from': case.beneficiary_name, 'to': data['name']}
        case.beneficiary_name = data['name']

    if 'phone' in data and data['phone'] != case.beneficiary_phone:
        changes['phone'] = {'from': case.beneficiary_phone, 'to': data['phone']}
        case.beneficiary_phone = data['phone']

    if 'id_number' in data and data['id_number'] != case.beneficiary_id_number:
        changes['id_number'] = {'from': case.beneficiary_id_number, 'to': data['id_number']}
        case.beneficiary_id_number = data['id_number']

    if 'address' in data and data['address'] != case.beneficiary_address:
        changes['address'] = {'from': case.beneficiary_address, 'to': data['address']}
        case.beneficiary_address = data['address']

    if 'case_type' in data:
        new_type = CaseType(data['case_type'])
        if new_type != case.case_type:
            changes['case_type'] = {'from': case.case_type.value, 'to': new_type.value}
            case.case_type = new_type

    db.session.commit()
    return changes


def assign_case(case, researcher_id):
    """Assign case to a researcher"""
    case.assigned_to = researcher_id
    case.status = CaseStatus.ASSIGNED
    db.session.commit()


def reassign_case(case, new_researcher_id):
    """Reassign case to a different researcher"""
    old_researcher_id = case.assigned_to
    case.assigned_to = new_researcher_id
    db.session.commit()
    return old_researcher_id


def move_to_investigating(case):
    """Move case to investigating status"""
    case.status = CaseStatus.INVESTIGATING
    db.session.commit()


def move_to_pending_approval(case):
    """Move case to pending approval status"""
    case.status = CaseStatus.PENDING_APPROVAL
    db.session.commit()


def move_to_pending_payment(case):
    """Move case to pending payment status"""
    case.status = CaseStatus.PENDING_PAYMENT
    db.session.commit()


def close_case(case):
    """Close the case"""
    case.status = CaseStatus.CLOSED
    db.session.commit()


def get_cases_for_user(user):
    """Get cases based on user role"""
    from ..utils.constants import UserRole

    if user.role == UserRole.RESEARCHER:
        # Researchers only see their assigned cases
        return Case.query.filter_by(assigned_to=user.id).order_by(Case.created_at.desc())

    # Owner and all managers can see all cases
    return Case.query.order_by(Case.created_at.desc())


def search_cases(query_string, user):
    """Search cases by various fields"""
    from ..utils.constants import UserRole

    base_query = Case.query

    # Filter for researchers
    if user.role == UserRole.RESEARCHER:
        base_query = base_query.filter_by(assigned_to=user.id)

    # Search across multiple fields
    search = f'%{query_string}%'
    results = base_query.filter(
        db.or_(
            Case.case_number.ilike(search),
            Case.beneficiary_name.ilike(search),
            Case.beneficiary_phone.ilike(search),
            Case.beneficiary_id_number.ilike(search),
            Case.beneficiary_address.ilike(search)
        )
    ).order_by(Case.created_at.desc())

    return results
