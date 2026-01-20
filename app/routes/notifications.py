from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models.notification import Notification
from ..utils.decorators import get_current_user

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user's notifications"""
    current_user = get_current_user()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    query = Notification.query.filter_by(user_id=current_user.id)

    if unread_only:
        query = query.filter_by(is_read=False)

    query = query.order_by(Notification.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get count of unread notifications"""
    current_user = get_current_user()

    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    return jsonify({'unread_count': count}), 200


@bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark a notification as read"""
    current_user = get_current_user()

    notification = Notification.query.get(notification_id)

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    if notification.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    notification.is_read = True
    db.session.commit()

    return jsonify({
        'message': 'Notification marked as read',
        'notification': notification.to_dict()
    }), 200


@bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read"""
    current_user = get_current_user()

    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})

    db.session.commit()

    return jsonify({'message': 'All notifications marked as read'}), 200


@bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Delete a notification"""
    current_user = get_current_user()

    notification = Notification.query.get(notification_id)

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    if notification.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    db.session.delete(notification)
    db.session.commit()

    return jsonify({'message': 'Notification deleted'}), 200
