from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..utils.constants import UserRole


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.Enum(UserRole), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_users = db.relationship('User', backref=db.backref('creator', remote_side=[id]))
    cases_created = db.relationship('Case', backref='creator', foreign_keys='Case.created_by')
    cases_assigned = db.relationship('Case', backref='researcher', foreign_keys='Case.assigned_to')
    reports = db.relationship('ResearcherReport', backref='researcher')
    approvals = db.relationship('ManagerApproval', backref='manager')
    finance_actions = db.relationship('FinanceAction', backref='finance_manager')
    audit_logs = db.relationship('AuditLog', backref='user')
    notifications = db.relationship('Notification', backref='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role.value if self.role else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_sensitive:
            data['created_by'] = self.created_by
        return data

    def __repr__(self):
        return f'<User {self.username}>'
