"""
Seed script to populate database with fake data
Run with: python seed_data.py
"""
import random
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.case import Case
from app.models.researcher_report import ResearcherReport
from app.models.manager_approval import ManagerApproval
from app.models.finance_action import FinanceAction
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.utils.constants import (
    UserRole, CaseType, CaseStatus, ApprovalDecision,
    Recommendation, FinanceStatus, AuditAction,
    REQUIRED_MANAGERS_DONATION, REQUIRED_MANAGERS_MEDICAL
)

# Arabic names for beneficiaries
ARABIC_FIRST_NAMES = [
    'محمد', 'أحمد', 'علي', 'حسن', 'حسين', 'عمر', 'خالد', 'يوسف', 'إبراهيم', 'عبدالله',
    'فاطمة', 'عائشة', 'مريم', 'زينب', 'خديجة', 'سارة', 'نور', 'ليلى', 'هدى', 'أمل',
    'سعيد', 'ماجد', 'فهد', 'سلطان', 'راشد', 'سالم', 'جابر', 'ناصر', 'بدر', 'طلال'
]

ARABIC_LAST_NAMES = [
    'العلي', 'المحمد', 'الأحمد', 'السالم', 'الناصر', 'العمري', 'الخالدي', 'الراشد',
    'الحسن', 'الحسين', 'البكري', 'الشمري', 'العتيبي', 'القحطاني', 'الدوسري',
    'المطيري', 'الحربي', 'الغامدي', 'الزهراني', 'السبيعي'
]

ADDRESSES = [
    'شارع الملك فهد، حي النزهة',
    'شارع الأمير سلطان، حي السلامة',
    'طريق الملك عبدالعزيز، حي الروضة',
    'شارع التحلية، حي الصفا',
    'شارع فلسطين، حي الجامعة',
    'حي الشرفية، شارع الستين',
    'حي البوادي، شارع المكرونة',
    'حي الفيصلية، شارع الأمير ماجد',
    'حي المروة، طريق المدينة',
    'حي الربوة، شارع حراء'
]

CITIES = ['جدة', 'مكة المكرمة', 'الرياض', 'الدمام', 'المدينة المنورة']

OPINIONS = [
    'تم التحقق من الحالة وهي بحاجة ماسة للمساعدة. الأسرة تعاني من ظروف مادية صعبة.',
    'بعد الزيارة الميدانية تبين أن الحالة مستحقة للدعم. المنزل في حالة سيئة ويحتاج للصيانة.',
    'الحالة تستحق المساعدة. الأب مريض ولا يستطيع العمل والأم هي المعيل الوحيد.',
    'تم التأكد من صحة المعلومات. الأسرة لديها أطفال في المدارس ولا تستطيع تحمل المصاريف.',
    'حالة إنسانية مستحقة. المريض يحتاج لعلاج مستمر وتكاليف الأدوية مرتفعة.',
    'بعد البحث والتحري تبين أن الأسرة فعلاً بحاجة للمساعدة العاجلة.',
    'الحالة تستوفي شروط الاستحقاق. تم التحقق من جميع المستندات المقدمة.',
    'زيارة ميدانية أكدت الاحتياج. الأسرة تسكن في شقة صغيرة وإيجارها متأخر.',
    'تم التواصل مع الجيران وأكدوا حاجة الأسرة للمساعدة.',
    'الحالة مستحقة بناءً على التقييم الميداني والمستندات المقدمة.'
]

REJECTION_REASONS = [
    'المعلومات المقدمة غير مكتملة',
    'يرجى إرفاق مستندات إضافية',
    'المبلغ المطلوب يحتاج لمراجعة',
    'يرجى التحقق من رقم الهوية',
    'العنوان غير واضح'
]

def generate_phone():
    return f"05{random.randint(10000000, 99999999)}"

def generate_id_number():
    return f"{random.randint(1000000000, 2999999999)}"

def generate_case_number(index):
    return f"CASE-2024-{str(index).zfill(5)}"

def random_date(start_days_ago=90, end_days_ago=0):
    days_ago = random.randint(end_days_ago, start_days_ago)
    return datetime.utcnow() - timedelta(days=days_ago)

def seed_database():
    app = create_app()

    with app.app_context():
        print("Starting database seeding...")

        # Get users
        owner = User.query.filter_by(role=UserRole.OWNER).first()
        manager1 = User.query.filter_by(role=UserRole.MANAGER_1).first()
        manager2 = User.query.filter_by(role=UserRole.MANAGER_2).first()
        manager3 = User.query.filter_by(role=UserRole.MANAGER_3).first()
        manager4 = User.query.filter_by(role=UserRole.MANAGER_4).first()
        manager5 = User.query.filter_by(role=UserRole.MANAGER_5).first()
        researcher = User.query.filter_by(role=UserRole.RESEARCHER).first()

        if not all([owner, manager1, manager2, manager3, manager4, manager5, researcher]):
            print("Error: Default users not found. Please run the app first to create them.")
            return

        print(f"Found users: owner={owner.id}, managers={manager1.id}-{manager5.id}, researcher={researcher.id}")

        # Check if already seeded
        existing_cases = Case.query.count()
        if existing_cases > 10:
            print(f"Database already has {existing_cases} cases. Skipping seed.")
            return

        cases_to_create = []

        # Create 50 cases with various statuses
        print("Creating 50 cases...")

        for i in range(1, 51):
            case_type = random.choice([CaseType.MEDICAL, CaseType.DONATION])

            # Determine status distribution
            status_weights = [
                (CaseStatus.NEW, 5),
                (CaseStatus.PENDING_DATA, 5),
                (CaseStatus.ASSIGNED, 8),
                (CaseStatus.INVESTIGATING, 8),
                (CaseStatus.PENDING_APPROVAL, 10),
                (CaseStatus.APPROVED, 8),
                (CaseStatus.PENDING_PAYMENT, 6),
                (CaseStatus.CLOSED, 15),
                (CaseStatus.REJECTED, 5),
            ]
            statuses = [s for s, w in status_weights for _ in range(w)]
            status = random.choice(statuses)

            first_name = random.choice(ARABIC_FIRST_NAMES)
            last_name = random.choice(ARABIC_LAST_NAMES)
            full_name = f"{first_name} {last_name}"
            address = f"{random.choice(ADDRESSES)}، {random.choice(CITIES)}"

            created_at = random_date(90, 1)

            case = Case(
                case_number=generate_case_number(i + existing_cases),
                case_type=case_type,
                status=status,
                beneficiary_name=full_name if status not in [CaseStatus.NEW] else None,
                beneficiary_phone=generate_phone() if status not in [CaseStatus.NEW] else None,
                beneficiary_id_number=generate_id_number() if status not in [CaseStatus.NEW] else None,
                beneficiary_address=address if status not in [CaseStatus.NEW] else None,
                amount_approved=random.choice([1000, 2000, 3000, 5000, 7000, 10000, 15000, 20000]) if status in [CaseStatus.APPROVED, CaseStatus.PENDING_PAYMENT, CaseStatus.CLOSED] else None,
                created_by=owner.id,
                assigned_to=researcher.id if status not in [CaseStatus.NEW, CaseStatus.PENDING_DATA] else None,
                created_at=created_at,
                updated_at=created_at + timedelta(days=random.randint(0, 10))
            )

            db.session.add(case)
            cases_to_create.append((case, status, case_type))

        db.session.flush()  # Get IDs for cases
        print(f"Created {len(cases_to_create)} cases")

        # Add researcher reports for cases that need them
        print("Creating researcher reports...")
        reports_created = 0
        for case, status, case_type in cases_to_create:
            if status in [CaseStatus.PENDING_APPROVAL, CaseStatus.APPROVED, CaseStatus.PENDING_PAYMENT, CaseStatus.CLOSED, CaseStatus.REJECTED]:
                report = ResearcherReport(
                    case_id=case.id,
                    researcher_id=researcher.id,
                    verified_name=case.beneficiary_name,
                    verified_phone=case.beneficiary_phone,
                    verified_id_number=case.beneficiary_id_number,
                    verified_address=case.beneficiary_address,
                    opinion=random.choice(OPINIONS),
                    recommendation=Recommendation.DESERVES if status != CaseStatus.REJECTED else random.choice([Recommendation.DESERVES, Recommendation.NOT_DESERVES]),
                    images_count=random.randint(2, 8),
                    created_at=case.created_at + timedelta(days=random.randint(1, 5))
                )
                db.session.add(report)
                reports_created += 1

        print(f"Created {reports_created} researcher reports")

        # Add manager approvals
        print("Creating manager approvals...")
        approvals_created = 0
        for case, status, case_type in cases_to_create:
            if status in [CaseStatus.PENDING_APPROVAL, CaseStatus.APPROVED, CaseStatus.PENDING_PAYMENT, CaseStatus.CLOSED, CaseStatus.REJECTED]:
                required_managers = REQUIRED_MANAGERS_DONATION if case_type == CaseType.DONATION else REQUIRED_MANAGERS_MEDICAL

                manager_map = {
                    UserRole.MANAGER_1: manager1,
                    UserRole.MANAGER_2: manager2,
                    UserRole.MANAGER_3: manager3,
                    UserRole.MANAGER_4: manager4,
                }

                for role in required_managers:
                    manager = manager_map.get(role)
                    if not manager:
                        continue

                    # Determine decision based on case status
                    if status == CaseStatus.PENDING_APPROVAL:
                        # Some approved, some pending
                        decision = random.choice([ApprovalDecision.APPROVED, ApprovalDecision.PENDING, ApprovalDecision.PENDING])
                    elif status == CaseStatus.REJECTED:
                        decision = ApprovalDecision.REJECTED
                    else:
                        decision = ApprovalDecision.APPROVED

                    approval = ManagerApproval(
                        case_id=case.id,
                        manager_id=manager.id if decision != ApprovalDecision.PENDING else None,
                        manager_role=role.value,
                        decision=decision,
                        amount_suggested=random.choice([1000, 2000, 3000, 5000, 7000, 10000]) if decision == ApprovalDecision.APPROVED else None,
                        rejection_reason=random.choice(REJECTION_REASONS) if decision == ApprovalDecision.REJECTED else None,
                        created_at=case.created_at + timedelta(days=random.randint(5, 10))
                    )
                    db.session.add(approval)
                    approvals_created += 1

        print(f"Created {approvals_created} manager approvals")

        # Add finance actions for paid/closed cases
        print("Creating finance actions...")
        finance_created = 0
        for case, status, case_type in cases_to_create:
            if status in [CaseStatus.PENDING_PAYMENT, CaseStatus.CLOSED]:
                finance = FinanceAction(
                    case_id=case.id,
                    finance_manager_id=manager5.id,
                    status=FinanceStatus.PAID if status == CaseStatus.CLOSED else FinanceStatus.READY_TO_PAY,
                    notes="تم صرف المبلغ بنجاح" if status == CaseStatus.CLOSED else None,
                    paid_at=case.updated_at if status == CaseStatus.CLOSED else None,
                    created_at=case.created_at + timedelta(days=random.randint(10, 15))
                )
                db.session.add(finance)
                finance_created += 1

        print(f"Created {finance_created} finance actions")

        # Add audit logs
        print("Creating audit logs...")
        logs_created = 0
        for case, status, case_type in cases_to_create:
            # Case created log
            log = AuditLog(
                case_id=case.id,
                user_id=owner.id,
                action=AuditAction.CASE_CREATED,
                created_at=case.created_at
            )
            log.set_details({"message": f"تم إنشاء الحالة {case.case_number}"})
            db.session.add(log)
            logs_created += 1

            if status not in [CaseStatus.NEW, CaseStatus.PENDING_DATA]:
                log = AuditLog(
                    case_id=case.id,
                    user_id=manager1.id,
                    action=AuditAction.CASE_ASSIGNED,
                    created_at=case.created_at + timedelta(days=1)
                )
                log.set_details({"message": "تم تعيين الباحث للحالة", "researcher_id": researcher.id})
                db.session.add(log)
                logs_created += 1

            if status in [CaseStatus.PENDING_APPROVAL, CaseStatus.APPROVED, CaseStatus.PENDING_PAYMENT, CaseStatus.CLOSED]:
                log = AuditLog(
                    case_id=case.id,
                    user_id=researcher.id,
                    action=AuditAction.INVESTIGATION_SUBMITTED,
                    created_at=case.created_at + timedelta(days=3)
                )
                log.set_details({"message": "تم تقديم تقرير البحث"})
                db.session.add(log)
                logs_created += 1

            if status == CaseStatus.CLOSED:
                log = AuditLog(
                    case_id=case.id,
                    user_id=manager5.id,
                    action=AuditAction.PAYMENT_CONFIRMED,
                    created_at=case.updated_at
                )
                log.set_details({"message": "تم تأكيد الدفع", "amount": case.amount_approved})
                db.session.add(log)
                logs_created += 1

        print(f"Created {logs_created} audit logs")

        # Commit all changes
        db.session.commit()

        print("\n" + "="*50)
        print("Database seeding completed successfully!")
        print("="*50)
        print(f"Total cases: {Case.query.count()}")
        print(f"Total reports: {ResearcherReport.query.count()}")
        print(f"Total approvals: {ManagerApproval.query.count()}")
        print(f"Total finance actions: {FinanceAction.query.count()}")
        print(f"Total audit logs: {AuditLog.query.count()}")
        print("="*50)

if __name__ == '__main__':
    seed_database()
