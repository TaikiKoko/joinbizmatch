from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.message import Message
from app.models.chat_room import ChatRoom
from app.models.user import User
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat/<int:partner_id>')
@login_required
def chat_room(partner_id):
    # パートナーユーザーの取得
    partner = User.query.get_or_404(partner_id)
    
    # ブロック状態のチェック
    if not current_user.can_message(partner):
        flash('このユーザーとはメッセージのやり取りができません。', 'error')
        return redirect(url_for('main.mypage'))
    
    # チャットルームの取得または作成
    chat_room = ChatRoom.query.filter(
        ((ChatRoom.company_id == current_user.id) & (ChatRoom.successor_id == partner_id)) |
        ((ChatRoom.company_id == partner_id) & (ChatRoom.successor_id == current_user.id))
    ).first()
    
    if not chat_room:
        chat_room = ChatRoom(
            company_id=min(current_user.id, partner_id),
            successor_id=max(current_user.id, partner_id)
        )
        db.session.add(chat_room)
        db.session.commit()
    
    # メッセージ履歴の取得
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == partner_id)) |
        ((Message.sender_id == partner_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at).all()
    
    # 未読メッセージを既読に更新
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.id,
        sender_id=partner_id,
        is_read=False
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    
    return render_template('main/chat_room.html',
                         chat_partner_id=partner_id,
                         messages=messages)

@chat_bp.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not content or not receiver_id:
        return jsonify({'status': 'error', 'message': '必要なデータが不足しています'}), 400
    
    # 受信者の取得とブロックチェック
    receiver = User.query.get_or_404(receiver_id)
    if not current_user.can_message(receiver):
        return jsonify({'status': 'error', 'message': 'このユーザーとはメッセージのやり取りができません'}), 403
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    
    # チャットルームの最終メッセージ時間を更新
    chat_room = ChatRoom.query.filter(
        ((ChatRoom.company_id == current_user.id) & (ChatRoom.successor_id == receiver_id)) |
        ((ChatRoom.company_id == receiver_id) & (ChatRoom.successor_id == current_user.id))
    ).first()
    
    if chat_room:
        chat_room.last_message_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': message.to_dict()
    })

@chat_bp.route('/api/messages/read', methods=['POST'])
@login_required
def mark_as_read():
    data = request.get_json()
    message_ids = data.get('message_ids', [])
    
    if not message_ids:
        return jsonify({'status': 'error', 'message': 'メッセージIDが指定されていません'}), 400
    
    Message.query.filter(
        Message.id.in_(message_ids),
        Message.receiver_id == current_user.id
    ).update({Message.is_read: True}, synchronize_session=False)
    
    db.session.commit()
    return jsonify({'status': 'success'})

# WebSocket関連の実装（オプション - 既存のWebSocket実装がある場合は統合）
from flask_socketio import emit, join_room, leave_room

def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')
    
    @socketio.on('message')
    def handle_message(data):
        receiver_id = data['receiver_id']
        emit('new_message', data, room=f'user_{receiver_id}') 