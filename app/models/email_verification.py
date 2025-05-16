from datetime import datetime, timedelta
from app import db

class EmailVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    new_email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False)

    def is_valid(self):
        """トークンの有効性をチェック（24時間以内で未使用）"""
        return (not self.is_used and 
                datetime.utcnow() - self.created_at < timedelta(hours=24))

    def mark_as_used(self):
        """トークンを使用済みとしてマーク"""
        self.is_used = True
        db.session.commit() 