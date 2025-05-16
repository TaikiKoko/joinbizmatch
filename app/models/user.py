from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from app import login_manager
from app.models.blocked_user import BlockedUser
from flask import url_for

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(20), nullable=True, default='successor')  # 'company' or 'successor'
    avatar_url = db.Column(db.String(200), nullable=True, default=None)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', back_populates='user', uselist=False, cascade='all, delete-orphan')
    favorite_companies = db.relationship('Company',
                                       secondary='company_favorites',
                                       lazy='dynamic',
                                       back_populates='favorited_by')
    successor = db.relationship('Successor', back_populates='user', uselist=False, cascade='all, delete-orphan')
    favorite_successors = db.relationship('Successor',
                                        secondary='successor_favorites',
                                        lazy='dynamic',
                                        back_populates='favorited_by')
    sent_messages = db.relationship('Message', 
                                  foreign_keys='Message.sender_id',
                                  back_populates='sender',
                                  lazy='dynamic',
                                  cascade='all, delete-orphan')
    received_messages = db.relationship('Message',
                                      foreign_keys='Message.recipient_id',
                                      back_populates='recipient',
                                      lazy='dynamic',
                                      cascade='all, delete-orphan')
    notifications = db.relationship('Notification',
                                  back_populates='user',
                                  lazy='dynamic',
                                  cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def __init__(self, username, email, user_type='successor'):
        self.username = username
        self.email = email
        self.user_type = user_type

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_avatar_url(self):
        """アバター画像のURLを取得（常に絶対パスで返す）"""
        if self.avatar_url:
            # static/が重複しないように調整
            avatar_path = self.avatar_url
            if avatar_path.startswith('static/'):
                avatar_path = avatar_path[len('static/'):]
            return url_for('static', filename=avatar_path)
        return url_for('static', filename='images/default_avatar.png')

    def to_dict(self):
        """APIレスポンス用の辞書を返す"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'user_type': self.user_type or 'successor',
            'avatar_url': self.get_avatar_url(),
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'last_seen': self.last_seen.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @property
    def is_company(self):
        """ユーザーが企業かどうかを判定"""
        return self.user_type == 'company'

    @property
    def is_successor(self):
        """ユーザーが後継者かどうかを判定"""
        return self.user_type in [None, 'successor']

    def has_completed_profile(self):
        """ユーザータイプに応じてプロフィール完了状態を確認"""
        if self.user_type == 'company':
            return self.company and self.company.is_profile_completed
        elif self.user_type == 'successor':
            return self.successor and self.successor.is_profile_completed
        return False

    def block_user(self, user):
        """ユーザーをブロックする"""
        if not self.is_blocking(user):
            block = BlockedUser(blocker_id=self.id, blocked_id=user.id)
            db.session.add(block)
            db.session.commit()

    def unblock_user(self, user):
        """ユーザーのブロックを解除する"""
        block = BlockedUser.query.filter_by(blocker_id=self.id, blocked_id=user.id).first()
        if block:
            db.session.delete(block)
            db.session.commit()

    def is_blocking(self, user):
        """指定したユーザーをブロックしているかどうかを確認"""
        if not user:
            return False
        return BlockedUser.query.filter_by(blocker_id=self.id, blocked_id=user.id).first() is not None

    def is_blocked_by(self, user):
        """指定したユーザーにブロックされているかどうかを確認"""
        if not user:
            return False
        return BlockedUser.query.filter_by(blocker_id=user.id, blocked_id=self.id).first() is not None

    def can_message(self, user):
        """指定したユーザーとメッセージのやり取りが可能かどうかを確認"""
        if not user:
            return False
        return not (self.is_blocking(user) or self.is_blocked_by(user))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))