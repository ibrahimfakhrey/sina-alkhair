from ..extensions import db
from ..models.notification import Notification
from ..models.user import User
from ..utils.constants import UserRole
from .fcm_service import send_push_to_user


def create_notification(user_id, title, message, case_id=None):
    """Create a notification for a user and send push notification"""
    # Save to database
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        case_id=case_id
    )
    db.session.add(notification)
    db.session.commit()

    # Send push notification
    try:
        user = User.query.get(user_id)
        if user and user.fcm_token:
            data = {'notification_id': str(notification.id)}
            if case_id:
                data['case_id'] = str(case_id)
            send_push_to_user(user, title, message, data)
    except Exception as e:
        print(f"Error sending push notification: {e}")

    return notification


def notify_managers_1_2(title, message, case_id=None):
    """Notify manager 1 and 2"""
    managers = User.query.filter(
        User.role.in_([UserRole.MANAGER_1, UserRole.MANAGER_2]),
        User.is_active == True
    ).all()

    for manager in managers:
        create_notification(manager.id, title, message, case_id)


def notify_case_created(case):
    """Notify managers about new case"""
    notify_managers_1_2(
        title='حالة جديدة',
        message=f'تم إنشاء حالة جديدة برقم {case.case_number}',
        case_id=case.id
    )


def notify_case_assigned(case, researcher):
    """Notify researcher about case assignment"""
    create_notification(
        user_id=researcher.id,
        title='حالة جديدة مُسندة إليك',
        message=f'تم إسناد الحالة رقم {case.case_number} إليك للبحث',
        case_id=case.id
    )


def notify_case_reassigned(case, old_researcher, new_researcher):
    """Notify researchers about reassignment"""
    if old_researcher:
        create_notification(
            user_id=old_researcher.id,
            title='تم إعادة إسناد الحالة',
            message=f'تم إعادة إسناد الحالة رقم {case.case_number} إلى باحث آخر',
            case_id=case.id
        )

    create_notification(
        user_id=new_researcher.id,
        title='حالة جديدة مُسندة إليك',
        message=f'تم إسناد الحالة رقم {case.case_number} إليك للبحث',
        case_id=case.id
    )


def notify_investigation_submitted(case):
    """Notify managers about investigation submission"""
    from ..utils.constants import CaseType

    # Notify manager 1, 2
    notify_managers_1_2(
        title='تم تقديم تقرير البحث',
        message=f'تم تقديم تقرير البحث للحالة رقم {case.case_number}',
        case_id=case.id
    )

    # Notify manager 3 or 4 based on case type
    if case.case_type == CaseType.DONATION:
        manager_role = UserRole.MANAGER_3
    else:
        manager_role = UserRole.MANAGER_4

    manager = User.query.filter_by(role=manager_role, is_active=True).first()
    if manager:
        create_notification(
            user_id=manager.id,
            title='حالة تحتاج موافقتك',
            message=f'الحالة رقم {case.case_number} تحتاج موافقتك',
            case_id=case.id
        )


def notify_case_approved(case):
    """Notify finance manager about approved case"""
    finance_manager = User.query.filter_by(role=UserRole.MANAGER_5, is_active=True).first()
    if finance_manager:
        create_notification(
            user_id=finance_manager.id,
            title='حالة معتمدة تحتاج صرف',
            message=f'الحالة رقم {case.case_number} معتمدة وتحتاج صرف مبلغ {case.amount_approved}',
            case_id=case.id
        )


def notify_case_rejected(case, managers_to_notify):
    """Notify managers about rejection"""
    for manager_id in managers_to_notify:
        create_notification(
            user_id=manager_id,
            title='تم رفض الحالة',
            message=f'تم رفض الحالة رقم {case.case_number} وتحتاج مراجعة',
            case_id=case.id
        )


def notify_payment_confirmed(case):
    """Notify owner about payment"""
    owner = User.query.filter_by(role=UserRole.OWNER, is_active=True).first()
    if owner:
        create_notification(
            user_id=owner.id,
            title='تم تأكيد الدفع',
            message=f'تم تأكيد صرف مبلغ {case.amount_approved} للحالة رقم {case.case_number}',
            case_id=case.id
        )


def notify_case_closed(case):
    """Notify owner and involved managers about case closure"""
    owner = User.query.filter_by(role=UserRole.OWNER, is_active=True).first()
    if owner:
        create_notification(
            user_id=owner.id,
            title='تم إغلاق الحالة',
            message=f'تم إغلاق الحالة رقم {case.case_number} بنجاح',
            case_id=case.id
        )

    # Notify managers 1 and 2
    notify_managers_1_2(
        title='تم إغلاق الحالة',
        message=f'تم إغلاق الحالة رقم {case.case_number} بنجاح',
        case_id=case.id
    )
