import secrets
from datetime import datetime, timedelta
from app.models.email_verification import EmailVerification
from app import db

def generate_verification_token():
    """ランダムなトークンを生成"""
    return secrets.token_urlsafe(32)

def create_verification_record(user_id, new_email):
    """メール確認用のレコードを作成"""
    token = generate_verification_token()
    verification = EmailVerification(
        user_id=user_id,
        new_email=new_email,
        token=token
    )
    db.session.add(verification)
    db.session.commit()
    return token

def verify_token(token):
    """トークンを検証し、有効な場合はユーザーIDと新しいメールアドレスを返す"""
    verification = EmailVerification.query.filter_by(token=token).first()
    if verification and verification.is_valid():
        verification.mark_as_used()
        return verification.user_id, verification.new_email
    return None, None 