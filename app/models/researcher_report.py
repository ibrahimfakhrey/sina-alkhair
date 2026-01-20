from datetime import datetime
from ..extensions import db
from ..utils.constants import Recommendation


class ResearcherReport(db.Model):
    __tablename__ = 'researcher_reports'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), unique=True, nullable=False)
    researcher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Verified beneficiary info
    verified_name = db.Column(db.String(100), nullable=True)
    verified_phone = db.Column(db.String(20), nullable=True)
    verified_id_number = db.Column(db.String(50), nullable=True)
    verified_address = db.Column(db.Text, nullable=True)

    # Researcher's assessment
    opinion = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Enum(Recommendation), nullable=True)
    images_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'researcher_id': self.researcher_id,
            'researcher_name': self.researcher.full_name if self.researcher else None,
            'verified_name': self.verified_name,
            'verified_phone': self.verified_phone,
            'verified_id_number': self.verified_id_number,
            'verified_address': self.verified_address,
            'opinion': self.opinion,
            'recommendation': self.recommendation.value if self.recommendation else None,
            'images_count': self.images_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<ResearcherReport for Case {self.case_id}>'
