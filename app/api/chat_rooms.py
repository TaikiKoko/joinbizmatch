from flask import jsonify, request, g
from app import db
from app.api import bp
from app.models import ChatRoom, Message, User
from app.api.errors import error_response, bad_request
from app.api.auth import token_auth

@bp.route('/chat/rooms', methods=['GET'])
@token_auth.login_required
def get_chat_rooms():
    """現在のユーザーのチャットルーム一覧を取得"""
    current_user = g.current_user
    
    # 企業または後継者として参加しているチャットルームを取得
    chat_rooms = ChatRoom.query.filter(
        (ChatRoom.company_id == current_user.id) |
        (ChatRoom.successor_id == current_user.id)
    ).order_by(ChatRoom.last_message_at.desc()).all()

    return jsonify({
        'chat_rooms': [room.to_dict() for room in chat_rooms]
    })

@bp.route('/chat/rooms/<int:user_id>', methods=['POST'])
@token_auth.login_required
def create_chat_room(user_id):
    """指定したユーザーとのチャットルームを作成または取得"""
    current_user = g.current_user
    
    # 自分自身とのチャットを防止
    if current_user.id == user_id:
        return bad_request('Cannot create chat room with yourself')

    # 相手ユーザーの存在確認
    other_user = User.query.get_or_404(user_id)

    # チャットルームを取得または作成
    # 企業と後継者の関係に基づいて適切な順序で作成
    if current_user.is_company and not other_user.is_company:
        chat_room = ChatRoom.get_or_create_room(company_id=current_user.id, successor_id=user_id)
    elif not current_user.is_company and other_user.is_company:
        chat_room = ChatRoom.get_or_create_room(company_id=user_id, successor_id=current_user.id)
    else:
        return bad_request('Invalid user combination for chat room')

    return jsonify(chat_room.to_dict())

@bp.route('/chat/rooms/<int:room_id>', methods=['GET'])
@token_auth.login_required
def get_chat_room(room_id):
    """特定のチャットルームの詳細を取得"""
    current_user = g.current_user
    chat_room = ChatRoom.query.get_or_404(room_id)

    # アクセス権限の確認
    if current_user.id not in [chat_room.company_id, chat_room.successor_id]:
        return error_response(403, 'Not authorized to access this chat room')

    # 未読メッセージを既読に更新
    unread_messages = Message.query.filter_by(
        chat_room_id=room_id,
        recipient_id=current_user.id,
        is_read=False
    ).all()

    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()

    return jsonify(chat_room.to_dict()) 