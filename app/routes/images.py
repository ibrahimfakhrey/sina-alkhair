from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
import os
from ..extensions import db
from ..models.case import Case
from ..models.case_image import CaseImage
from ..utils.constants import UserRole, ImageType
from ..utils.decorators import role_required, get_current_user
from ..utils.helpers import save_uploaded_file, delete_file
from ..services import audit_service

bp = Blueprint('images', __name__, url_prefix='/api')


@bp.route('/cases/<int:case_id>/images', methods=['POST'])
@jwt_required()
def upload_images(case_id):
    """Upload images for a case"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    # Check permissions based on role
    if current_user.role == UserRole.RESEARCHER:
        if case.assigned_to != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        default_type = ImageType.INVESTIGATION
    elif current_user.role in [UserRole.OWNER, UserRole.MANAGER_1, UserRole.MANAGER_2]:
        default_type = ImageType.SCREENSHOT
    elif current_user.role == UserRole.MANAGER_5:
        default_type = ImageType.PAYMENT_PROOF
    else:
        return jsonify({'error': 'You cannot upload images'}), 403

    if 'images' not in request.files and 'image' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400

    # Get image type from form
    image_type_str = request.form.get('image_type', default_type.value)
    try:
        image_type = ImageType(image_type_str)
    except ValueError:
        image_type = default_type

    uploaded_images = []
    files = request.files.getlist('images') or [request.files.get('image')]

    for file in files:
        if file:
            image_path = save_uploaded_file(file, image_type)
            if image_path:
                case_image = CaseImage(
                    case_id=case.id,
                    image_path=image_path,
                    image_type=image_type,
                    uploaded_by=current_user.id
                )
                db.session.add(case_image)
                uploaded_images.append(case_image)

                # Log
                audit_service.log_image_uploaded(case, current_user, image_type.value)

    db.session.commit()

    return jsonify({
        'message': f'{len(uploaded_images)} image(s) uploaded successfully',
        'images': [img.to_dict() for img in uploaded_images]
    }), 201


@bp.route('/cases/<int:case_id>/images', methods=['GET'])
@jwt_required()
def get_case_images(case_id):
    """Get all images for a case"""
    current_user = get_current_user()
    case = Case.query.get(case_id)

    if not case:
        return jsonify({'error': 'Case not found'}), 404

    # Check permissions
    if current_user.role == UserRole.RESEARCHER and case.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    images = CaseImage.query.filter_by(case_id=case_id).order_by(CaseImage.created_at.desc()).all()

    return jsonify({
        'images': [img.to_dict() for img in images]
    }), 200


@bp.route('/images/<int:image_id>', methods=['GET'])
@jwt_required()
def get_image(image_id):
    """Get a single image file"""
    current_user = get_current_user()
    image = CaseImage.query.get(image_id)

    if not image:
        return jsonify({'error': 'Image not found'}), 404

    case = Case.query.get(image.case_id)

    # Check permissions
    if current_user.role == UserRole.RESEARCHER and case.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    # Construct full path
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    full_path = os.path.join(base_path, image.image_path)

    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(full_path)


@bp.route('/images/<int:image_id>/info', methods=['GET'])
@jwt_required()
def get_image_info(image_id):
    """Get image metadata"""
    current_user = get_current_user()
    image = CaseImage.query.get(image_id)

    if not image:
        return jsonify({'error': 'Image not found'}), 404

    case = Case.query.get(image.case_id)

    # Check permissions
    if current_user.role == UserRole.RESEARCHER and case.assigned_to != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({'image': image.to_dict()}), 200


@bp.route('/images/<int:image_id>', methods=['DELETE'])
@jwt_required()
@role_required(UserRole.OWNER, UserRole.MANAGER_1, UserRole.MANAGER_2, UserRole.RESEARCHER)
def delete_image(image_id):
    """Delete an image"""
    current_user = get_current_user()
    image = CaseImage.query.get(image_id)

    if not image:
        return jsonify({'error': 'Image not found'}), 404

    case = Case.query.get(image.case_id)

    # Researchers can only delete their own images
    if current_user.role == UserRole.RESEARCHER:
        if image.uploaded_by != current_user.id:
            return jsonify({'error': 'You can only delete your own images'}), 403

    # Delete file from storage
    delete_file(image.image_path)

    # Log before deleting from DB
    audit_service.log_image_deleted(case, current_user, image_id)

    # Delete from database
    db.session.delete(image)
    db.session.commit()

    return jsonify({'message': 'Image deleted successfully'}), 200
