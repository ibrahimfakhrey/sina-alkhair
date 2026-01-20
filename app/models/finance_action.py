from datetime import datetime
from ..extensions import db
from ..utils.constants import FinanceStatus


class FinanceAction(db.Model):
    __tablename__ = 'finance_actions'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), unique=True, nullable=False)
    finance_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Status
    status = db.Column(db.Enum(FinanceStatus), default=FinanceStatus.READY_TO_PAY, nullable=False)

    # Payment proof
    proof_image_path = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Timestamps
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'finance_manager_id': self.finance_manager_id,
            'finance_manager_name': self.finance_manager.full_name if self.finance_manager else None,
            'status': self.status.value if self.status else None,
            'proof_image_path': self.proof_image_path,
            'notes': self.notes,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<FinanceAction for Case {self.case_id}>'
