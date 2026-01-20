import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from .constants import CaseType, ImageType


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_case_number(case_type, db):
    """Generate case number like MED-2026-0001 or DON-2026-0001"""
    from ..models.case import Case

    year = datetime.now().year
    prefix = 'MED' if case_type == CaseType.MEDICAL else 'DON'

    # Get the last case number for this type and year
    last_case = Case.query.filter(
        Case.case_number.like(f'{prefix}-{year}-%')
    ).order_by(Case.id.desc()).first()

    if last_case:
        last_number = int(last_case.case_number.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1

    return f'{prefix}-{year}-{new_number:04d}'


def save_uploaded_file(file, image_type):
    """Save uploaded file and return the path"""
    if not file or not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"

    # Determine folder based on image type
    if image_type == ImageType.SCREENSHOT:
        folder = 'screenshots'
    elif image_type == ImageType.PAYMENT_PROOF:
        folder = 'payment_proofs'
    else:
        folder = 'investigations'

    upload_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'uploads',
        folder
    )

    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    return os.path.join('uploads', folder, unique_filename)


def delete_file(file_path):
    """Delete a file from storage"""
    if file_path:
        full_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            file_path
        )
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    return False
