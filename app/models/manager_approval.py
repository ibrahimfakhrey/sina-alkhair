from datetime import datetime
from ..extensions import db
from ..utils.constants import ApprovalDecision


class ManagerApproval(db.Model):
    __tablename__ = 'manager_approvals'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    manager_role = db.Column(db.String(20), nullable=False)

    # Decision
    decision = db.Column(db.Enum(ApprovalDecision), default=ApprovalDecision.PENDING, nullable=False)
    amount_suggested = db.Column(db.Float, nullable=True)

    # Rejection details
    rejection_reason = db.Column(db.Text, nullable=True)
    suggestion = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one approval per manager per case
    __table_args__ = (
        db.UniqueConstraint('case_id', 'manager_role', name='unique_case_manager_role'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'manager_id': self.manager_id,
            'manager_name': self.manager.full_name if self.manager else None,
            'manager_role': self.manager_role,
            'decision': self.decision.value if self.decision else None,
            'amount_suggested': self.amount_suggested,
            'rejection_reason': self.rejection_reason,
            'suggestion': self.suggestion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<ManagerApproval {self.manager_role} for Case {self.case_id}>'
