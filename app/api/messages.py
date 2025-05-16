from flask import jsonify, request, g
from app import db
from app.api import bp
from app.models import Message, ChatRoom
from app.api.errors import error_response, bad_request
from app.api.auth import token_auth
from app.utils.notifications import notify_message
from flask_login import current_user, login_required

@bp.route('/chat/rooms/<int:room_id>/messages', methods=['GET'])
@token_auth.login_required
def get_messages(room_id):
    """チャットルームのメッセージ一覧を取得"""
    current_user = g.current_user
    chat_room = ChatRoom.query.get_or_404(room_id)

    # アクセス権限の確認
    if current_user.id not in [chat_room.company_id, chat_room.successor_id]:
        return error_response(403, 'Not authorized to access this chat room')

    # ページネーションパラメータ
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    # メッセージを取得（新しい順）
    messages = Message.query.filter_by(chat_room_id=room_id)\
        .order_by(Message.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    # 未読メッセージを既読に更新
    unread_messages = Message.query.filter_by(
        chat_room_id=room_id,
        recipient_id=current_user.id,
        is_read=False
    ).all()

    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()

    return jsonify({
        'items': [message.to_dict() for message in messages.items],
        'total': messages.total,
        'pages': messages.pages,
        'current_page': messages.page
    })

@bp.route('/chat/rooms/<int:room_id>/messages', methods=['POST'])
@token_auth.login_required
def send_message(room_id):
    """メッセージを送信"""
    current_user = g.current_user
    chat_room = ChatRoom.query.get_or_404(room_id)

    # アクセス権限の確認
    if current_user.id not in [chat_room.company_id, chat_room.successor_id]:
        return error_response(403, 'Not authorized to access this chat room')

    # リクエストデータの検証
    data = request.get_json() or {}
    if 'content' not in data or not data['content'].strip():
        return bad_request('Message content is required')

    # 受信者を特定
    recipient_id = chat_room.successor_id if current_user.id == chat_room.company_id else chat_room.company_id

    # メッセージを作成
    message = Message(
        chat_room_id=room_id,
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=data['content'].strip()
    )
    db.session.add(message)

    # チャットルームの最終メッセージ時刻を更新
    chat_room.last_message_at = message.created_at
    db.session.commit()

    # 通知を作成
    notify_message(message)

    return jsonify(message.to_dict()), 201

@bp.route('/messages/<int:message_id>/read', methods=['PUT'])
@token_auth.login_required
def mark_message_read(message_id):
    """メッセージを既読にする"""
    current_user = g.current_user
    message = Message.query.get_or_404(message_id)

    # アクセス権限の確認
    if message.recipient_id != current_user.id:
        return error_response(403, 'Not authorized to mark this message as read')

    message.is_read = True
    db.session.commit()

    return jsonify(message.to_dict())

@bp.route('/chat/unread_counts')
@login_required
def get_unread_counts():
    if current_user.user_type == 'company':
        chat_rooms = ChatRoom.query.filter_by(user1_id=current_user.id).all()
    else:
        chat_rooms = ChatRoom.query.filter_by(user2_id=current_user.id).all()
    unread_counts = {}
    for room in chat_rooms:
        unread_count = Message.query.filter_by(
            chat_room_id=room.id,
            is_read=False
        ).filter(Message.sender_id != current_user.id).count()
        unread_counts[room.id] = unread_count
    return jsonify(unread_counts) 