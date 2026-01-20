from datetime import datetime
from ..extensions import db
from ..utils.constants import ImageType


class CaseImage(db.Model):
    __tablename__ = 'case_images'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    image_type = db.Column(db.Enum(ImageType), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to uploader
    uploader = db.relationship('User', backref='uploaded_images')

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'image_path': self.image_path,
            'image_type': self.image_type.value if self.image_type else None,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.full_name if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<CaseImage {self.id} for Case {self.case_id}>'
