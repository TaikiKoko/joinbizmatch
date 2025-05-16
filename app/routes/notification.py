from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models.notification import Notification
from app import db

bp = Blueprint('notification', __name__)

@bp.route('/notifications')
@login_required
def list_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('notifications/list.html', notifications=notifications)

@bp.route('/notifications/unread')
@login_required
def get_unread_count():
    count = current_user.notifications.filter_by(is_read=False).count()
    return jsonify({'count': count})

@bp.route('/notifications/mark-read/<int:id>', methods=['POST'])
@login_required
def mark_as_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        return jsonify({'error': '権限がありません。'}), 403
    
    notification.is_read = True
    db.session.commit()
    return jsonify({'message': '通知を既読にしました。'})

@bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_as_read():
    current_user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'すべての通知を既読にしました。'}) 