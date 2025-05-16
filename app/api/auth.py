from flask import g
from flask_httpauth import HTTPTokenAuth
from app.models.user import User
from app.api.errors import error_response

token_auth = HTTPTokenAuth()

@token_auth.verify_token
def verify_token(token):
    """トークンを検証し、ユーザーを返す"""
    user = User.verify_auth_token(token) if token else None
    if user:
        g.current_user = user
        return user
    return None

@token_auth.error_handler
def token_auth_error():
    """認証エラーハンドラ"""
    return error_response(401) 