from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.chat import bp
from app.models.chat_room import ChatRoom
from app.models.message import Message
from app.models.user import User
from datetime import datetime
from app.models.attachment import Attachment
from app.utils.attachments import save_attachment, delete_attachment, format_file_size
from app.utils.notifications import notify_message
from app.chat.cache import (
    cache,
    CACHE_TTL,
    serialize_message,
    deserialize_message
)
import os
from werkzeug.utils import secure_filename

@bp.route('/')
@login_required
def chat_list():
    """チャットルーム一覧を表示"""
    if current_user.is_company:
        # 企業ユーザーの場合は必ずuser1_idで検索
        chat_rooms = ChatRoom.query.filter(
            ChatRoom.user1_id == current_user.id
        ).order_by(ChatRoom.last_message_at.desc()).all()
    else:
        # 後継者ユーザーの場合はuser2_idで検索
        chat_rooms = ChatRoom.query.filter(
            ChatRoom.user2_id == current_user.id
        ).order_by(ChatRoom.last_message_at.desc()).all()
    
    return render_template('chat/chat_list.html', chat_rooms=chat_rooms)

@bp.route('/start/<int:user_id>')
@login_required
def start(user_id):
    """チャットを開始し、チャットルームにリダイレクト"""
    try:
        current_app.logger.info(f'Starting chat: current_user={current_user.id}({current_user.user_type}), other_user={user_id}')
        
        if user_id == current_user.id:
            flash('自分自身とチャットはできません。', 'error')
            return redirect(url_for('main.index'))
        
        other_user = User.query.get_or_404(user_id)
        current_app.logger.info(f'Other user found: {other_user.id}({other_user.user_type})')
        
        # 企業と後継者の組み合わせをチェック
        if current_user.user_type == other_user.user_type:
            flash('同じユーザータイプ間でのチャットはできません。', 'error')
            return redirect(url_for('main.index'))
        
        # 既存のチャットルームを検索
        existing_room = ChatRoom.query.filter(
            ((ChatRoom.user1_id == current_user.id) & (ChatRoom.user2_id == user_id)) |
            ((ChatRoom.user1_id == user_id) & (ChatRoom.user2_id == current_user.id))
        ).first()
        
        if existing_room:
            current_app.logger.info(f'Found existing chat room: {existing_room.id}')
            return redirect(url_for('chat.room', room_id=existing_room.id))
        
        # 新しいチャットルームを作成
        if current_user.user_type == 'company':
            user1_id = current_user.id
            user2_id = other_user.id
        else:
            user1_id = other_user.id
            user2_id = current_user.id
        
        current_app.logger.info(f'Creating new chat room: user1_id={user1_id}(company), user2_id={user2_id}(successor)')
        
        chat_room = ChatRoom(
            user1_id=user1_id,
            user2_id=user2_id
        )
        
        try:
            db.session.add(chat_room)
            db.session.commit()
            current_app.logger.info(f'Successfully created chat room: {chat_room.id}')
            return redirect(url_for('chat.room', room_id=chat_room.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Failed to create chat room: {str(e)}')
            flash('チャットルームを作成できませんでした。', 'error')
            return redirect(url_for('main.index'))
        
    except Exception as e:
        current_app.logger.error(f'Error in start_chat: {str(e)}')
        flash('チャットルームの作成中にエラーが発生しました。', 'error')
        return redirect(url_for('main.index'))

@bp.route('/room/<int:room_id>')
@login_required
def room(room_id):
    """チャットルームを表示"""
    chat_room = ChatRoom.query.get_or_404(room_id)
    
    if not chat_room.can_access(current_user.id):
        flash('このチャットルームにアクセスする権限がありません。', 'error')
        return redirect(url_for('main.index'))
    
    other_user = chat_room.get_other_user(current_user.id)
    messages = Message.query.filter_by(chat_room_id=room_id).order_by(Message.created_at.asc()).all()
    
    # デバッグ用のログ出力を追加
    current_app.logger.info(f'Chat room {room_id}: Found {len(messages)} messages')
    current_app.logger.info(f'Current user: {current_user.id}, Other user: {other_user.id}')
    
    # 未読メッセージを既読に更新
    try:
        unread_messages = Message.query.filter_by(
            chat_room_id=room_id,
            recipient_id=current_user.id,
            is_read=False
        ).all()
        
        current_app.logger.info(f'Found {len(unread_messages)} unread messages for user {current_user.id}')
        
        for message in unread_messages:
            message.is_read = True
            current_app.logger.info(f'Marking message {message.id} as read')
        
        db.session.commit()
        current_app.logger.info('Successfully updated message read status')
        
    except Exception as e:
        current_app.logger.error(f'Error updating message read status: {str(e)}')
        db.session.rollback()
    
    return render_template('chat/chat_room.html',
                         chat_room=chat_room,
                         other_user=other_user,
                         messages=messages)

@bp.route('/api/chat/rooms/<int:room_id>/messages', methods=['GET'])
@login_required
def get_room_messages(room_id):
    """特定のチャットルームのメッセージ一覧を取得"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    chat_room = ChatRoom.query.get_or_404(room_id)
    
    if not chat_room.can_access(current_user.id):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    cache_key = f"chat:room:{room_id}:messages:page:{page}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify({
            'messages': [deserialize_message(msg) for msg in cached_data],
            'has_more': len(cached_data) == per_page
        })
    
    # メッセージを取得（新しい順）
    messages = Message.query.filter_by(chat_room_id=room_id)\
        .order_by(Message.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # メッセージをキャッシュに保存
    if messages.items:
        serialized_messages = [serialize_message(msg) for msg in messages.items]
        cache.set(cache_key, serialized_messages, CACHE_TTL)
    
    return jsonify({
        'messages': [message.to_dict() for message in messages.items],
        'total': messages.total,
        'pages': messages.pages,
        'current_page': messages.page,
        'has_more': messages.has_next
    })

@bp.route('/room/<int:room_id>/send', methods=['POST'])
@login_required
def send_message(room_id):
    """メッセージを送信"""
    chat_room = ChatRoom.query.get_or_404(room_id)
    
    if not chat_room.can_access(current_user.id):
        return jsonify({'error': 'アクセス権限がありません。'}), 403
    
    content = request.form.get('content')
    if not content or not content.strip():
        return jsonify({'error': 'メッセージを入力してください。'}), 400
    
    other_user = chat_room.get_other_user(current_user.id)
    message = Message(
        chat_room_id=room_id,
        sender_id=current_user.id,
        recipient_id=other_user.id,
        content=content
    )
    
    # デバッグ用のログ出力を追加
    current_app.logger.info(f'Sending message in room {room_id}: from {current_user.username} to {other_user.username}')
    current_app.logger.info(f'Message content: {content[:50]}...')
    
    db.session.add(message)
    db.session.commit()
    
    # メッセージ送信後のログ出力
    current_app.logger.info(f'Message {message.id} sent successfully')
    
    chat_room.last_message_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'sender_id': message.sender_id,
        'created_at': message.created_at.isoformat()
    })

@bp.route('/api/messages/<int:message_id>/read', methods=['GET', 'PUT'])
@login_required
def message_read_status(message_id):
    """メッセージの既読状態を管理"""
    message = Message.query.get_or_404(message_id)
    chat_room = ChatRoom.query.get(message.chat_room_id)
    
    if not chat_room.can_access(current_user.id):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    if request.method == 'GET':
        cache_key = f"chat:message:{message_id}:read"
        cached_status = cache.get(cache_key)
        if cached_status is not None:
            return jsonify({'is_read': bool(int(cached_status))})
        return jsonify({'is_read': message.is_read})
    else:
        try:
            message.mark_as_read()
            cache_key = f"chat:message:{message_id}:read"
            cache.set(cache_key, '1', CACHE_TTL)
            return jsonify({'success': True, 'is_read': True})
        except Exception as e:
            current_app.logger.error(f'Failed to update message read status: {str(e)}')
            return jsonify({'error': 'Failed to update read status'}), 500

@bp.route('/api/chat/rooms/<int:room_id>/unread', methods=['GET'])
@login_required
def get_unread_count(room_id):
    """未読メッセージ数を取得"""
    chat_room = ChatRoom.query.get_or_404(room_id)
    
    if not chat_room.can_access(current_user.id):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    unread_count = Message.get_unread_count(room_id, current_user.id)
    return jsonify({'unread_count': unread_count})

@bp.route('/api/chat/start/<int:user_id>', methods=['POST'])
@login_required
def start_chat_api(user_id):
    """新しいチャットを開始（API）"""
    if user_id == current_user.id:
        return jsonify({
            'status': 'error',
            'message': '自分自身とチャットはできません。'
        }), 400
    
    other_user = User.query.get_or_404(user_id)
    chat_room = ChatRoom.get_or_create_room(current_user.id, user_id)
    
    if chat_room is None:
        return jsonify({
            'status': 'error',
            'message': 'チャットルームを作成できませんでした。'
        }), 400
    
    return jsonify({
        'status': 'success',
        'chat_room': chat_room.to_dict(current_user.id)
    })

@bp.route('/chat/<int:chat_room_id>/upload', methods=['POST'])
@login_required
def upload_file(chat_room_id):
    """ファイルアップロード処理"""
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    # ファイルの検証
    if not allowed_file(file.filename):
        return jsonify({'error': '許可されていないファイル形式です'}), 400
    
    if file.content_length > MAX_FILE_SIZE:
        return jsonify({'error': 'ファイルサイズは10MB以下にしてください'}), 400
    
    # メッセージの作成
    message = Message(
        chat_room_id=chat_room_id,
        sender_id=current_user.id,
        content=''
    )
    db.session.add(message)
    db.session.commit()
    
    # ファイルの保存
    attachment = save_attachment(file, message.id)
    if not attachment:
        db.session.delete(message)
        db.session.commit()
        return jsonify({'error': 'ファイルの保存に失敗しました'}), 500
    
    # メッセージの更新
    message.content = f'ファイルを送信しました: {attachment.original_filename}'
    db.session.commit()
    
    # 通知の送信
    notify_message(message)
    
    return jsonify({
        'message': serialize_message(message),
        'attachment': {
            'id': attachment.id,
            'filename': attachment.original_filename,
            'file_path': attachment.file_path,
            'file_type': attachment.file_type,
            'file_size': attachment.file_size,
            'is_image': attachment.is_image
        }
    }) 