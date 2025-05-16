from flask import request, current_app
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import ChatRoom, Message, Notification
from app.utils.notifications import notify_message
from datetime import datetime
import logging
import json
from sqlalchemy.exc import SQLAlchemyError
import traceback

logger = logging.getLogger(__name__)

def log_event(event_type, data):
    """イベントログを詳細に記録"""
    try:
        log_data = {
            'event': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': current_user.id if current_user.is_authenticated else None,
            'data': data
        }
        logger.info(f"[WebSocket Event] {json.dumps(log_data, ensure_ascii=False)}")
    except Exception as e:
        logger.error(f"Logging error: {str(e)}")

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        logger.warning("Unauthenticated connection attempt")
        return False
    
    try:
        log_event('connect', {'user_id': current_user.id})
        return True
    except Exception as e:
        logger.error(f"Error in handle_connect: {str(e)}")
        return False

@socketio.on('disconnect')
def handle_disconnect():
    if not current_user.is_authenticated:
        return
    
    try:
        log_event('disconnect', {'user_id': current_user.id})
    except Exception as e:
        logger.error(f"Error in handle_disconnect: {str(e)}")

@socketio.on('join_chat')
def handle_join_chat(data):
    """チャットルームに参加"""
    if not current_user.is_authenticated:
        logger.warning("Unauthenticated join attempt")
        return {'error': 'Unauthorized'}, 401
    
    try:
        room_id = data.get('room_id')
        log_event('join_chat_attempt', {
            'room_id': room_id,
            'user_id': current_user.id
        })
        
        if not room_id:
            logger.error("Join attempt without room_id")
            return {'error': 'Room ID is required'}, 400
        
        chat_room = ChatRoom.query.get(room_id)
        if not chat_room:
            logger.error(f"Attempted to join non-existent room: {room_id}")
            return {'error': 'Chat room not found'}, 404
        
        if not chat_room.can_access(current_user.id):
            logger.warning(f"Access denied to room {room_id} for user {current_user.id}")
            return {'error': 'Access denied'}, 403
        
        room_channel = f'chat_room_{room_id}'
        join_room(room_channel)
        
        # 相手のユーザー情報を取得
        other_user = chat_room.get_other_user(current_user.id)
        
        # join_chat_success イベントを送信
        success_data = {
            'success': True,
            'room_id': room_id,
            'current_user_id': current_user.id,
            'other_user_id': other_user.id if other_user else None
        }
        emit('join_chat_success', success_data)
        log_event('join_chat_success', success_data)
        
        # 未読メッセージを既読に更新
        try:
            unread_messages = Message.query.filter_by(
                chat_room_id=room_id,
                recipient_id=current_user.id,
                is_read=False
            ).all()
            
            if unread_messages:
                message_ids = []
                for message in unread_messages:
                    message.is_read = True
                    message.read_at = datetime.utcnow()
                    message_ids.append(message.id)
                
                db.session.commit()
                log_event('messages_marked_read', {
                    'room_id': room_id,
                    'message_count': len(message_ids),
                    'message_ids': message_ids
                })
                
                # 既読通知を送信
                read_status_data = {
                    'message_ids': message_ids,
                    'reader_id': current_user.id,
                    'chat_room_id': room_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                emit('messages_read', read_status_data, room=room_channel)
                
        except Exception as e:
            logger.error(f"Error updating read status: {str(e)}")
            db.session.rollback()
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Error in handle_join_chat: {str(e)}")
        return {'error': 'Internal server error'}, 500

@socketio.on('leave_room')
def handle_leave_room(data):
    """チャットルームから退出"""
    if not current_user.is_authenticated:
        return
    
    try:
        room_id = data.get('room_id')
        if room_id:
            room_channel = f'chat_room_{room_id}'
            leave_room(room_channel)
            logger.info(f'User {current_user.id} left room {room_id}')
            emit('leave_confirmation', {'status': 'success', 'room_id': room_id})
    except Exception as e:
        logger.error(f'Error in handle_leave_room: {str(e)}')
        emit('error', {'message': 'Failed to leave chat room'})

@socketio.on('send_message')
def handle_send_message(data):
    """メッセージを送信"""
    if not current_user.is_authenticated:
        logger.warning("Unauthenticated message send attempt")
        return {'error': 'Unauthorized', 'success': False}
    
    try:
        room_id = data.get('room_id')
        content = data.get('content')
        log_event('message_send_attempt', {
            'room_id': room_id,
            'user_id': current_user.id,
            'content_length': len(content) if content else 0,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        if not room_id or not content:
            logger.error("Invalid message parameters")
            return {'error': 'Invalid parameters', 'success': False}
        
        chat_room = ChatRoom.query.get(room_id)
        if not chat_room:
            logger.error(f"Attempted to send message to non-existent room: {room_id}")
            return {'error': 'Chat room not found', 'success': False}
        
        if not chat_room.can_access(current_user.id):
            logger.warning(f"Message send attempt without permission: room {room_id}, user {current_user.id}")
            return {'error': 'Permission denied', 'success': False}
        
        try:
            # メッセージを作成
            message = Message(
                chat_room_id=room_id,
                sender_id=current_user.id,
                recipient_id=chat_room.get_other_user(current_user.id).id,
                content=content,
                created_at=datetime.utcnow()
            )
            
            # チャットルームの最終メッセージ時刻を更新
            chat_room.last_message_at = message.created_at
            
            db.session.add(message)
            db.session.commit()
            log_event('message_saved', {
                'message_id': message.id,
                'room_id': room_id,
                'sender_id': current_user.id,
                'recipient_id': message.recipient_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # メッセージデータの準備
            message_data = {
                'id': message.id,
                'chat_room_id': message.chat_room_id,
                'sender_id': message.sender_id,
                'recipient_id': message.recipient_id,
                'content': message.content,
                'is_read': False,
                'created_at': message.created_at.isoformat(),
                'sender': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'avatar_url': current_user.get_avatar_url()
                }
            }
            
            # WebSocketでメッセージをブロードキャスト
            room_channel = f'chat_room_{room_id}'
            try:
                # まず送信者に確認を送信
                emit('message_confirmation', {
                    'success': True,
                    'message': message_data
                })
                
                # 全員にブロードキャスト
                emit('new_message', message_data, room=room_channel)
                
                log_event('message_broadcast', {
                    'message_id': message.id,
                    'room_id': room_id,
                    'channel': room_channel,
                    'timestamp': datetime.utcnow().isoformat()
                })

                # 追加: 相手ユーザーの全クライアントに未読数更新イベントをemit
                recipient_room = f'user_{message.recipient_id}'
                # 受信者の全体未読数
                total_unread = Message.query.filter_by(recipient_id=message.recipient_id, is_read=False).count()
                # 受信者が参加している全ルームごとの未読数
                user_rooms = ChatRoom.query.filter((ChatRoom.user1_id==message.recipient_id)|(ChatRoom.user2_id==message.recipient_id)).all()
                room_counts = {}
                for room in user_rooms:
                    count = Message.query.filter_by(chat_room_id=room.id, recipient_id=message.recipient_id, is_read=False).count()
                    room_counts[str(room.id)] = count
                emit('update_unread_count', {'total_count': total_unread, 'room_counts': room_counts}, room=recipient_room)
                
                # デバッグログ
                log_event('update_unread_count_emit', {
                    'recipient_id': message.recipient_id,
                    'room_id': room_id,
                    'recipient_room': recipient_room,
                    'timestamp': datetime.utcnow().isoformat(),
                    'socket_id': request.sid
                })

                # 通知処理
                try:
                    message_preview = content[:30] + ('...' if len(content) > 30 else '')
                    chat_url = f'/chat/room/{room_id}'
                    notify_message(
                        user_id=message.recipient_id,
                        sender_name=current_user.username,
                        message_preview=message_preview,
                        chat_url=chat_url
                    )
                except Exception as notify_error:
                    logger.error(f"Failed to send notification: {str(notify_error)}")
                
                return {'success': True, 'message': message_data}
                
            except Exception as broadcast_error:
                logger.error(f"Broadcast error: {str(broadcast_error)}")
                return {'success': True, 'message': message_data, 'broadcast_error': str(broadcast_error)}
            
        except SQLAlchemyError as e:
            logger.error(f'Database error in handle_send_message: {str(e)}')
            db.session.rollback()
            return {'error': 'Failed to save message', 'success': False}
            
    except Exception as e:
        logger.error(f"Error in handle_send_message: {str(e)}")
        return {'error': str(e), 'success': False}

@socketio.on('chat_page_opened')
def handle_chat_page_opened(data):
    """チャットページが開かれたときの処理"""
    logger.info(f"[CHAT_PAGE_OPENED] Received event with data: {data}")
    
    if not current_user.is_authenticated:
        logger.warning("[CHAT_PAGE_OPENED] Unauthorized access attempt")
        return {'error': 'Unauthorized'}, 401
    
    try:
        room_id = data.get('room_id')
        user_id = data.get('user_id')
        
        logger.info(f"[CHAT_PAGE_OPENED] Processing for room_id={room_id}, user_id={user_id}")
        
        if not room_id or not user_id:
            logger.error(f"[CHAT_PAGE_OPENED] Invalid parameters: {data}")
            return {'error': 'Invalid parameters'}, 400
            
        # チャットルームを取得
        chat_room = ChatRoom.query.get(room_id)
        if not chat_room:
            logger.error(f"[CHAT_PAGE_OPENED] Chat room not found: {room_id}")
            return {'error': 'Chat room not found'}, 404
            
        # 相手のユーザーIDを取得
        other_user = chat_room.get_other_user(user_id)
        if not other_user:
            logger.error(f"[CHAT_PAGE_OPENED] Other user not found in room {room_id}")
            return {'error': 'Other user not found'}, 404
            
        # 未読メッセージを既読に更新
        unread_messages = Message.query.filter_by(
            chat_room_id=room_id,
            sender_id=other_user.id,
            recipient_id=user_id,
            is_read=False
        ).all()
        
        logger.info(f"[CHAT_PAGE_OPENED] Found {len(unread_messages)} unread messages")
        
        if unread_messages:
            message_ids = []
            for message in unread_messages:
                message.is_read = True
                message.read_at = datetime.utcnow()
                message_ids.append(message.id)
            
            try:
                db.session.commit()
                logger.info(f"[CHAT_PAGE_OPENED] Marked {len(message_ids)} messages as read in room {room_id}")
                
                # 既読状態の更新を通知
                room_channel = f'chat_room_{room_id}'
                read_status_data = {
                    'message_ids': message_ids,
                    'reader_id': user_id,
                    'chat_room_id': room_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # ルーム内のメンバーにのみ通知を送信
                emit('messages_read', read_status_data, to=room_channel)
                logger.info(f"[CHAT_PAGE_OPENED] Sent read status update to room {room_channel}: {read_status_data}")
                
            except Exception as e:
                logger.error(f"[CHAT_PAGE_OPENED] Error updating read status: {str(e)}")
                db.session.rollback()
                return {'error': 'Database error'}, 500
        else:
            logger.info("[CHAT_PAGE_OPENED] No unread messages to update")
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"[CHAT_PAGE_OPENED] Error in handle_chat_page_opened: {str(e)}")
        logger.error(f"[CHAT_PAGE_OPENED] Traceback: {traceback.format_exc()}")
        return {'error': 'Internal server error'}, 500

@socketio.on('mark_as_read')
def handle_mark_as_read(data):
    try:
        message_id = data.get('message_id')
        chat_room_id = data.get('chat_room_id')

        if not message_id or not chat_room_id:
            return {'error': 'Missing message_id or chat_room_id'}

        message = Message.query.get(message_id)
        if not message:
            return {'error': 'Message not found'}

        message.is_read = True
        db.session.commit()

        room_channel = f'chat_room_{chat_room_id}'
        read_status_data = {
            'message_ids': [message_id],
            'reader_id': current_user.id,
            'chat_room_id': chat_room_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        emit('messages_read', read_status_data, room=room_channel)

    except Exception as e:
        logger.error(f'Error in handle_mark_as_read: {str(e)}')
        return {'error': 'Internal server error'}

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """ユーザールームに参加"""
    if not current_user.is_authenticated:
        logger.warning("Unauthenticated user room join attempt")
        return {'error': 'Unauthorized'}, 401
    
    try:
        user_id = data.get('user_id')
        if not user_id:
            logger.error("Join attempt without user_id")
            return {'error': 'User ID is required'}, 400
        
        if user_id != current_user.id:
            logger.warning(f"Access denied to user room {user_id} for user {current_user.id}")
            return {'error': 'Access denied'}, 403
        
        user_room = f'user_{user_id}'
        join_room(user_room)
        
        # 詳細なログ
        log_data = {
            'user_id': current_user.id,
            'room': user_room,
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'socket_id': request.sid
        }
        logger.info(f'User {current_user.id} joined user room {user_room}')
        log_event('join_user_room', log_data)
        
        return {'success': True, 'room': user_room}
        
    except Exception as e:
        error_msg = f"Error in handle_join_user_room: {str(e)}"
        logger.error(error_msg)
        log_event('join_user_room_error', {
            'error': error_msg,
            'user_id': current_user.id if current_user.is_authenticated else None
        })
        return {'error': 'Internal server error'}, 500 