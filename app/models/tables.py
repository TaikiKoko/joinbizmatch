from datetime import datetime
from app import db

# お気に入りの中間テーブル定義
company_favorites = db.Table('company_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('company_id', db.Integer, db.ForeignKey('companies.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

successor_favorites = db.Table('successor_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('successor_id', db.Integer, db.ForeignKey('successors.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
) 