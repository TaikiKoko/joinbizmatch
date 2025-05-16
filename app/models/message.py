from datetime import datetime
from app import db

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ - 文字列参照を使用して循環インポートを回避
    chat_room = db.relationship('ChatRoom', back_populates='messages')
    sender = db.relationship('User', 
                           foreign_keys=[sender_id], 
                           back_populates='sent_messages',
                           lazy='joined')
    recipient = db.relationship('User', 
                              foreign_keys=[recipient_id], 
                              back_populates='received_messages',
                              lazy='joined')

    def __repr__(self):
        return f'<Message {self.id}>'

    def to_dict(self):
        """メッセージをJSON形式に変換"""
        return {
            'id': self.id,
            'chat_room_id': self.chat_room_id,
            'sender': {
                'id': self.sender.id,
                'username': self.sender.username,
                'avatar_url': self.sender.get_avatar_url()
            },
            'recipient': {
                'id': self.recipient.id,
                'username': self.recipient.username,
                'avatar_url': self.recipient.get_avatar_url()
            },
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def mark_as_read(self):
        """メッセージを既読にする"""
        if not self.is_read:
            self.is_read = True
            db.session.commit()

    @classmethod
    def get_unread_count(cls, chat_room_id, user_id):
        """指定されたチャットルームの未読メッセージ数を取得する"""
        return cls.query.filter(
            cls.chat_room_id == chat_room_id,
            cls.sender_id != user_id,
            cls.is_read == False
        ).count() 