from enum import Enum


class UserRole(str, Enum):
    OWNER = 'owner'
    MANAGER_1 = 'manager_1'
    MANAGER_2 = 'manager_2'
    MANAGER_3 = 'manager_3'  # Donation cases
    MANAGER_4 = 'manager_4'  # Medical cases
    MANAGER_5 = 'manager_5'  # Finance
    RESEARCHER = 'researcher'


class CaseType(str, Enum):
    MEDICAL = 'medical'
    DONATION = 'donation'


class CaseStatus(str, Enum):
    NEW = 'new'                           # Just created (screenshot by owner)
    PENDING_DATA = 'pending_data'         # Manager filling data
    ASSIGNED = 'assigned'                 # Assigned to researcher
    INVESTIGATING = 'investigating'       # Researcher working
    PENDING_APPROVAL = 'pending_approval' # Waiting for managers
    APPROVED = 'approved'                 # All managers approved
    PENDING_PAYMENT = 'pending_payment'   # Waiting for finance
    CLOSED = 'closed'                     # Case completed
    REJECTED = 'rejected'                 # Rejected (can retry)


class ApprovalDecision(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class Recommendation(str, Enum):
    DESERVES = 'deserves'
    NOT_DESERVES = 'not_deserves'


class ImageType(str, Enum):
    SCREENSHOT = 'screenshot'
    INVESTIGATION = 'investigation'
    MEDICAL_REPORT = 'medical_report'
    PROOF_DOCUMENT = 'proof_document'
    PAYMENT_PROOF = 'payment_proof'


class FinanceStatus(str, Enum):
    READY_TO_PAY = 'ready_to_pay'
    PAID = 'paid'


class AuditAction(str, Enum):
    CASE_CREATED = 'case_created'
    CASE_UPDATED = 'case_updated'
    CASE_ASSIGNED = 'case_assigned'
    CASE_REASSIGNED = 'case_reassigned'
    INVESTIGATION_SUBMITTED = 'investigation_submitted'
    INVESTIGATION_UPDATED = 'investigation_updated'
    CASE_APPROVED = 'case_approved'
    CASE_REJECTED = 'case_rejected'
    PAYMENT_CONFIRMED = 'payment_confirmed'
    CASE_CLOSED = 'case_closed'
    IMAGE_UPLOADED = 'image_uploaded'
    IMAGE_DELETED = 'image_deleted'


# Managers required for each case type
REQUIRED_MANAGERS_DONATION = [UserRole.MANAGER_1, UserRole.MANAGER_2, UserRole.MANAGER_3]
REQUIRED_MANAGERS_MEDICAL = [UserRole.MANAGER_1, UserRole.MANAGER_2, UserRole.MANAGER_4]
