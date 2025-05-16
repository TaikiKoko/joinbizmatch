from flask import current_app, url_for
from flask_login import current_user
from app import socketio, db
from flask_socketio import emit, join_room, leave_room, disconnect
from app.models.message import Message
from app.models.chat_room import ChatRoom
from functools import wraps
import traceback
from datetime import datetime

def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
            return
        return f(*args, **kwargs)
    return wrapped

@socketio.on('connect')
def handle_connect():
    """WebSocket接続時の処理"""
    if not current_user.is_authenticated:
        current_app.logger.warning('Unauthenticated user tried to connect')
        return False
    
    current_app.logger.info(f'[Connect] User {current_user.id} connected to WebSocket')
    return True

@socketio.on('disconnect')
@authenticated_only
def handle_disconnect():
    """クライアントが切断したときの処理"""
    try:
        current_app.logger.info(f'Client disconnected: {current_user.id}')
    except Exception as e:
        current_app.logger.error(f'Error in handle_disconnect: {str(e)}')
        current_app.logger.error(traceback.format_exc())

@socketio.on('join')
def handle_join(data):
    """チャットルームに参加"""
    if not current_user.is_authenticated:
        current_app.logger.warning('Unauthenticated user tried to join room')
        emit('join_error', {'error': 'Authentication required'})
        return

    try:
        room_id = str(data.get('room_id'))
        if not room_id:
            current_app.logger.error('No room_id provided')
            emit('join_error', {'error': 'Room ID is required'})
            return

        current_app.logger.info(f'[Join] User {current_user.id} joining room {room_id}')
        
        # チャットルームの存在確認
        chat_room = ChatRoom.query.get(room_id)
        if not chat_room:
            current_app.logger.error(f'Chat room {room_id} not found')
            emit('join_error', {'error': 'Chat room not found'})
            return

        # ルームに参加
        join_room(room_id)
        current_app.logger.info(f'[Join] User {current_user.id} successfully joined room {room_id}')
        
        # 参加確認メッセージを送信
        emit('join_confirmation', {
            'status': 'success',
            'room_id': room_id,
            'user_id': current_user.id
        })
        
    except Exception as e:
        current_app.logger.error(f'Error in handle_join: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        emit('join_error', {'error': 'Failed to join room'})

@socketio.on('leave')
@authenticated_only
def handle_leave(data):
    """チャットルームから退出"""
    try:
        room_id = data.get('room_id')
        if room_id:
            current_app.logger.info(f'User {current_user.id} leaving room {room_id}')
            leave_room(str(room_id))
            emit('user_left', 
                 {'user_id': current_user.id, 'room_id': room_id},
                 room=str(room_id),
                 include_self=False)
    except Exception as e:
        current_app.logger.error(f'Error in handle_leave: {str(e)}')
        current_app.logger.error(traceback.format_exc())

@socketio.on('join_user_room')
def handle_join_user_room(data):
    user_id = data.get('user_id')
    if user_id:
        join_room(f'user_{user_id}')
        emit('join_user_room_response', {'status': 'success'})

@socketio.on('new_message')
def handle_new_message(data):
    """新しいメッセージを受信したときの処理"""
    if not current_user.is_authenticated:
        current_app.logger.warning('Unauthenticated user tried to send message')
        emit('message_error', {'error': 'Authentication required'})
        return

    try:
        room_id = str(data.get('room_id'))
        content = data.get('message', '').strip()
        
        current_app.logger.info(f'[Step 1] Received new message from user {current_user.id} in room {room_id}: {content}')
        
        if not content:
            current_app.logger.error('Empty message content received')
            emit('message_error', {'error': 'Message content is required'})
            return

        # チャットルームの存在確認
        chat_room = ChatRoom.query.get(room_id)
        if not chat_room:
            current_app.logger.error(f'Chat room {room_id} not found')
            emit('message_error', {'error': 'Chat room not found'})
            return

        current_app.logger.info(f'[Step 2] Found chat room {room_id}')

        # メッセージの作成と保存
        try:
            message = Message(
                chat_room_id=int(room_id),
                sender_id=current_user.id,
                recipient_id=chat_room.get_other_user(current_user.id).id,
                content=content,
                created_at=datetime.utcnow()
            )
            
            db.session.add(message)
            db.session.commit()
            
            current_app.logger.info(f'[Step 3] Message saved to database with ID: {message.id}')

            # メッセージデータの作成
            message_data = {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender_id,
                'recipient_id': message.recipient_id,
                'created_at': message.created_at.isoformat(),
                'is_read': False,
                'sender': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'avatar_url': 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y'
                }
            }
            
            current_app.logger.info(f'[Step 4] Broadcasting message to room {room_id}')
            current_app.logger.info(f'Message data: {message_data}')
            
            # 同じルームの全員にメッセージをブロードキャスト
            emit('new_message', message_data, room=room_id, include_self=True)
            current_app.logger.info(f'[Step 5] Message {message.id} successfully broadcasted to room {room_id}')
            
            # 受信者の未読数をカウント
            unread_count = Message.query.filter_by(recipient_id=message.recipient_id, is_read=False).count()
            # 各ルームごとの未読数を取得
            chat_rooms = ChatRoom.query.filter((ChatRoom.user1_id==message.recipient_id)|(ChatRoom.user2_id==message.recipient_id)).all()
            room_counts = {}
            for room in chat_rooms:
                count = Message.query.filter_by(chat_room_id=room.id, recipient_id=message.recipient_id, is_read=False).count()
                room_counts[str(room.id)] = count
            current_app.logger.info(f'Emitting update_unread_count to user_{message.recipient_id} with total_count={unread_count}, room_counts={room_counts}')
            emit('update_unread_count', {'total_count': unread_count, 'room_counts': room_counts}, room=f'user_{message.recipient_id}')
            
        except Exception as e:
            current_app.logger.error(f'Database error: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            db.session.rollback()
            emit('message_error', {'error': 'Failed to save message'})
            return
            
    except Exception as e:
        current_app.logger.error(f'General error in handle_new_message: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        emit('message_error', {'error': 'Failed to process message'})

@socketio.on('mark_read')
@authenticated_only
def handle_mark_read(data):
    """メッセージを既読にする"""
    try:
        message_id = data.get('message_id')
        room_id = data.get('room_id')
        
        if not message_id or not room_id:
            return
            
        message = Message.query.get(message_id)
        if message and message.recipient_id == current_user.id and not message.is_read:
            message.is_read = True
            try:
                db.session.commit()
                current_app.logger.info(f'Message {message_id} marked as read')
                
                emit('message_read',
                     {'message_id': message_id},
                     room=str(room_id))

                # 既読処理後
                unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
                from app.models import ChatRoom
                chat_rooms = ChatRoom.query.filter((ChatRoom.user1_id==current_user.id)|(ChatRoom.user2_id==current_user.id)).all()
                room_counts = {}
                for room in chat_rooms:
                    count = Message.query.filter_by(chat_room_id=room.id, recipient_id=current_user.id, is_read=False).count()
                    room_counts[str(room.id)] = count
                current_app.logger.info(f'Emitting update_unread_count to user_{current_user.id} with total_count={unread_count}, room_counts={room_counts}')
                emit('update_unread_count', {'total_count': unread_count, 'room_counts': room_counts}, room=f'user_{current_user.id}')
                
            except Exception as e:
                current_app.logger.error(f'Error updating message {message_id}: {str(e)}')
                db.session.rollback()
                
    except Exception as e:
        current_app.logger.error(f'Error in handle_mark_read: {str(e)}')

@socketio.on('check_online')
def handle_check_online(data):
    """ユーザーのオンライン状態をチェック"""
    try:
        room_id = data.get('room_id')
        if room_id:
            current_app.logger.info(f'User {current_user.id} checking online status in room {room_id}')
            emit('user_online',
                 {'user_id': current_user.id, 'room_id': room_id},
                 room=str(room_id),
                 include_self=False)
    except Exception as e:
        current_app.logger.error(f'Error in handle_check_online: {str(e)}')

@socketio.on_error_default
def default_error_handler(e):
    """デフォルトのエラーハンドラ"""
    current_app.logger.error(f'WebSocket error: {str(e)}')
    current_app.logger.error(traceback.format_exc())
    emit('error', {'error': 'An unexpected error occurred'}) 