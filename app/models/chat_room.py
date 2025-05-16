from datetime import datetime
from app import db
from app.models.message import Message
from app.models.user import User

class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ - 文字列参照を使用して循環インポートを回避
    user1 = db.relationship('User', foreign_keys=[user1_id], lazy='joined', primaryjoin='ChatRoom.user1_id == User.id')
    user2 = db.relationship('User', foreign_keys=[user2_id], lazy='joined', primaryjoin='ChatRoom.user2_id == User.id')
    messages = db.relationship('Message', back_populates='chat_room', lazy='dynamic',
                             order_by='Message.created_at.desc()')

    def __repr__(self):
        return f'<ChatRoom {self.id}>'

    @classmethod
    def get_or_create_room(cls, user1_id, user2_id):
        """2人のユーザー間のチャットルームを取得または作成"""
        if user1_id == user2_id:
            return None

        # ユーザー情報を取得
        user1 = User.query.get(user1_id)
        user2 = User.query.get(user2_id)
        
        if not user1 or not user2:
            return None

        # 企業ユーザーを必ずuser1_idに設定
        if user2.is_company:
            user1_id, user2_id = user2_id, user1_id

        # 既存のチャットルームを検索
        room = cls.query.filter(
            ((cls.user1_id == user1_id) & (cls.user2_id == user2_id)) |
            ((cls.user1_id == user2_id) & (cls.user2_id == user1_id))
        ).first()

        if room is None:
            # 新しいチャットルームを作成
            room = cls(user1_id=user1_id, user2_id=user2_id)
            db.session.add(room)
            db.session.commit()
        elif not room.user1.is_company:
            # 既存のルームで企業ユーザーがuser2_idにいる場合は入れ替える
            old_user1_id = room.user1_id
            room.user1_id = room.user2_id
            room.user2_id = old_user1_id
            db.session.commit()

        return room

    def get_other_user(self, user_id):
        """指定されたユーザーの相手ユーザーを取得"""
        if str(user_id) == str(self.user1_id):
            return self.user2
        elif str(user_id) == str(self.user2_id):
            return self.user1
        return None

    def can_access(self, user_id):
        """ユーザーがこのチャットルームにアクセスできるかチェック"""
        return str(user_id) in (str(self.user1_id), str(self.user2_id))

    def to_dict(self, current_user_id):
        """チャットルームをJSON形式に変換"""
        other_user = self.get_other_user(current_user_id)
        last_message = self.messages.first()
        unread_count = self.messages.filter_by(
            recipient_id=current_user_id,
            is_read=False
        ).count()

        return {
            'id': self.id,
            'other_user': {
                'id': other_user.id,
                'username': other_user.username,
                'avatar_url': other_user.avatar_url if hasattr(other_user, 'avatar_url') else None,
                'user_type': other_user.user_type
            },
            'last_message': last_message.to_dict() if last_message else None,
            'unread_count': unread_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_message_at': self.last_message_at.isoformat()
        } 