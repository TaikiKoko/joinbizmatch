from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.notification import Notification
from app.utils.notifications import mark_notifications_as_read, get_unread_count

bp = Blueprint('notifications', __name__)

@bp.route('/api/notifications/unread-count')
@login_required
def get_unread_notification_count():
    count = get_unread_count(current_user.id)
    return jsonify({'count': count})

@bp.route('/api/notifications/recent')
@login_required
def get_recent_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return jsonify({
        'notifications': [{
            'id': n.id,
            'type': n.type,
            'content': n.content,
            'link': n.link,
            'read': n.read,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
    })

@bp.route('/api/notifications/<int:id>/read', methods=['POST'])
@login_required
def mark_notification_as_read(id):
    notification = Notification.query.get_or_404(id)
    
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    notification.read = True
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_as_read():
    mark_notifications_as_read(current_user.id)
    return jsonify({'success': True})

@bp.route('/notifications', methods=['GET'])
def get_notifications():
    notifications = Notification.query.all()
    return jsonify([notification.to_dict() for notification in notifications])

@bp.route('/notifications/<int:id>', methods=['GET'])
def get_notification(id):
    notification = Notification.query.get_or_404(id)
    return jsonify(notification.to_dict())

@bp.route('/notifications', methods=['POST'])
def create_notification():
    data = request.get_json()
    notification = Notification(
        user_id=data['user_id'],
        title=data['title'],
        content=data['content']
    )
    db.session.add(notification)
    db.session.commit()
    return jsonify(notification.to_dict()), 201

@bp.route('/notifications/<int:id>', methods=['PUT'])
def update_notification(id):
    notification = Notification.query.get_or_404(id)
    data = request.get_json()
    if 'title' in data:
        notification.title = data['title']
    if 'content' in data:
        notification.content = data['content']
    db.session.commit()
    return jsonify(notification.to_dict()) 