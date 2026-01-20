from datetime import datetime
from ..extensions import db
from ..utils.constants import AuditAction
import json


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.Enum(AuditAction), nullable=False)
    details = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_details(self, details_dict):
        """Set details from a dictionary"""
        self.details = json.dumps(details_dict, ensure_ascii=False)

    def get_details(self):
        """Get details as a dictionary"""
        if self.details:
            return json.loads(self.details)
        return {}

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_role': self.user.role.value if self.user and self.user.role else None,
            'action': self.action.value if self.action else None,
            'details': self.get_details(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<AuditLog {self.action} for Case {self.case_id}>'
