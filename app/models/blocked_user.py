from datetime import datetime
from app import db

class BlockedUser(db.Model):
    __tablename__ = 'blocked_users'

    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ
    blocker = db.relationship('User', foreign_keys=[blocker_id], backref=db.backref('blocking', lazy='dynamic'))
    blocked = db.relationship('User', foreign_keys=[blocked_id], backref=db.backref('blocked_by', lazy='dynamic'))

    def __repr__(self):
        return f'<BlockedUser {self.blocker_id} -> {self.blocked_id}>' 