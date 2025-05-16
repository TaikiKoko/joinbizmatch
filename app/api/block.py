from flask import jsonify, request
from flask_login import current_user, login_required
from app import db
from app.api import bp
from app.models.blocked_user import BlockedUser
from app.models.user import User

@bp.route('/block/<int:user_id>', methods=['POST', 'DELETE'])
@login_required
def handle_block(user_id):
    if user_id == current_user.id:
        return jsonify({
            'success': False,
            'message': '自分自身をブロックすることはできません'
        }), 400
    
    user = User.query.get_or_404(user_id)
    
    try:
        if request.method == 'POST':
            if not current_user.is_blocking(user):
                current_user.block_user(user)
                message = 'ユーザーをブロックしました'
            else:
                return jsonify({
                    'success': False,
                    'message': 'すでにブロックしています'
                }), 400
        else:  # DELETE
            if current_user.is_blocking(user):
                current_user.unblock_user(user)
                message = 'ブロックを解除しました'
            else:
                return jsonify({
                    'success': False,
                    'message': 'このユーザーはブロックされていません'
                }), 400
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': message,
            'blocked': current_user.is_blocking(user)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'エラーが発生しました',
            'error': str(e)
        }), 400

@bp.route('/blocks', methods=['GET'])
@login_required
def get_blocked_users():
    try:
        blocked_users = BlockedUser.query.filter_by(blocker_id=current_user.id).all()
        return jsonify({
            'success': True,
            'blocked_users': [{
                'id': block.blocked.id,
                'username': block.blocked.username,
                'blocked_at': block.created_at.isoformat() if block.created_at else None,
                'user_type': block.blocked.user_type
            } for block in blocked_users]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'ブロックリストの取得中にエラーが発生しました',
            'error': str(e)
        }), 500 