from datetime import datetime
from ..extensions import db
from ..utils.constants import CaseType, CaseStatus


class Case(db.Model):
    __tablename__ = 'cases'

    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True, nullable=False)
    case_type = db.Column(db.Enum(CaseType), nullable=False)
    status = db.Column(db.Enum(CaseStatus), default=CaseStatus.NEW, nullable=False)

    # Initial screenshot (optional if created by manager)
    initial_screenshot = db.Column(db.String(500), nullable=True)

    # Beneficiary info (nullable - filled later)
    beneficiary_name = db.Column(db.String(100), nullable=True)
    beneficiary_phone = db.Column(db.String(20), nullable=True)
    beneficiary_id_number = db.Column(db.String(50), nullable=True)
    beneficiary_address = db.Column(db.Text, nullable=True)

    # Financial info
    amount_approved = db.Column(db.Float, nullable=True)

    # Foreign keys
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images = db.relationship('CaseImage', backref='case', cascade='all, delete-orphan')
    report = db.relationship('ResearcherReport', backref='case', uselist=False, cascade='all, delete-orphan')
    approvals = db.relationship('ManagerApproval', backref='case', cascade='all, delete-orphan')
    finance_action = db.relationship('FinanceAction', backref='case', uselist=False, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='case', cascade='all, delete-orphan', order_by='AuditLog.created_at')
    notifications = db.relationship('Notification', backref='case', cascade='all, delete-orphan')

    def to_dict(self, include_details=False):
        data = {
            'id': self.id,
            'case_number': self.case_number,
            'case_type': self.case_type.value if self.case_type else None,
            'status': self.status.value if self.status else None,
            'beneficiary_name': self.beneficiary_name,
            'beneficiary_phone': self.beneficiary_phone,
            'beneficiary_id_number': self.beneficiary_id_number,
            'beneficiary_address': self.beneficiary_address,
            'amount_approved': self.amount_approved,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_details:
            data['initial_screenshot'] = self.initial_screenshot
            data['creator'] = self.creator.to_dict() if self.creator else None
            data['researcher'] = self.researcher.to_dict() if self.researcher else None
            data['images'] = [img.to_dict() for img in self.images]
            data['report'] = self.report.to_dict() if self.report else None
            data['approvals'] = [a.to_dict() for a in self.approvals]
            data['finance_action'] = self.finance_action.to_dict() if self.finance_action else None
            data['audit_logs'] = [log.to_dict() for log in self.audit_logs]

        return data

    def __repr__(self):
        return f'<Case {self.case_number}>'
