from flask import render_template, jsonify, request, abort
from flask_login import login_required, current_user
from app.models import User, ChatRoom, Message
from app import app
from app import db
from app.chat.cache import cache_messages, get_cached_messages, invalidate_room_cache

@app.route('/successors')
@login_required
def successors():
    # Get all users except the current user
    successors = User.query.filter(User.id != current_user.id).all()
    return render_template('successors.html', successors=successors)

@app.route('/api/chat/create', methods=['POST'])
@login_required
def create_chat_room():
    data = request.get_json()
    successor_id = data.get('successor_id')
    
    if not successor_id:
        return jsonify({'error': 'Successor ID is required'}), 400
        
    # 既存のチャットルームを確認
    existing_room = ChatRoom.query.filter(
        ((ChatRoom.user1_id == current_user.id) & (ChatRoom.user2_id == successor_id)) |
        ((ChatRoom.user1_id == successor_id) & (ChatRoom.user2_id == current_user.id))
    ).first()
    
    if existing_room:
        return jsonify({'room_id': existing_room.id})
    
    # 新しいチャットルームを作成
    new_room = ChatRoom(
        user1_id=current_user.id,
        user2_id=successor_id
    )
    db.session.add(new_room)
    db.session.commit()
    
    return jsonify({'room_id': new_room.id})

@app.route('/chat/<int:room_id>')
@login_required
def chat_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    
    # ユーザーがこのチャットルームのメンバーであることを確認
    if current_user.id not in [room.user1_id, room.user2_id]:
        abort(403)
    
    # チャット相手のユーザー情報を取得
    other_user_id = room.user2_id if current_user.id == room.user1_id else room.user1_id
    other_user = User.query.get(other_user_id)
    
    return render_template('chat.html', room=room, other_user=other_user)

@app.route('/api/chat/<int:room_id>/messages')
@login_required
def get_messages(room_id):
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # キャッシュからメッセージを取得
    cached_messages = get_cached_messages(room_id, page)
    if cached_messages is not None:
        return jsonify({'messages': cached_messages})
    
    # キャッシュにない場合はDBから取得
    room = ChatRoom.query.get_or_404(room_id)
    if current_user.id != room.user1_id and current_user.id != room.user2_id:
        abort(403)
    
    messages = Message.query.filter_by(room_id=room_id)\
        .order_by(Message.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    messages_list = [{
        'id': msg.id,
        'content': msg.content,
        'user_id': msg.user_id,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages.items]
    
    # メッセージをキャッシュに保存
    cache_messages(room_id, page, messages_list)
    
    return jsonify({'messages': messages_list})

@app.route('/api/chat/<int:room_id>/send', methods=['POST'])
@login_required
def send_message(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    if current_user.id != room.user1_id and current_user.id != room.user2_id:
        abort(403)
    
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'No message content provided'}), 400
    
    message = Message(
        content=data['content'],
        user_id=current_user.id,
        room_id=room_id
    )
    db.session.add(message)
    db.session.commit()
    
    # メッセージキャッシュを無効化
    invalidate_room_cache(room_id)
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'user_id': message.user_id,
        'timestamp': message.timestamp.isoformat()
    }) 