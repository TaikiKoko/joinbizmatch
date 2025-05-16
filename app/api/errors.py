from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

def error_response(status_code, message=None):
    """APIエラーレスポンスを生成する"""
    payload = {
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error'),
        'status': status_code
    }
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response

def bad_request(message):
    """400 Bad Request エラーを生成する"""
    return error_response(400, message)

def unauthorized(message="認証が必要です。"):
    """401 Unauthorized エラーを生成する"""
    return error_response(401, message)

def forbidden(message="アクセスが拒否されました。"):
    """403 Forbidden エラーを生成する"""
    return error_response(403, message)

def not_found(message="リソースが見つかりません。"):
    """404 Not Found エラーを生成する"""
    return error_response(404, message) 