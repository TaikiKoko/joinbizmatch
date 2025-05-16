import logging
from datetime import datetime
import json
from redis import Redis, ConnectionError
from flask import current_app

logger = logging.getLogger(__name__)

# キャッシュのTTL（24時間）
CACHE_TTL = 86400

class Cache:
    def __init__(self):
        self.redis = None
        self.fallback_cache = {}
        self.initialized = False

    def _initialize_redis(self):
        """Redisクライアントの初期化を試みる"""
        if self.initialized:
            return

        try:
            # アプリケーションコンテキストの存在を確認
            if not current_app:
                logger.warning("No application context available. Using in-memory cache.")
                self.redis = None
                return

            # 環境設定から接続情報を取得
            redis_host = current_app.config.get('REDIS_HOST', 'localhost')
            redis_port = current_app.config.get('REDIS_PORT', 6379)
            redis_db = current_app.config.get('REDIS_DB', 0)
            redis_password = current_app.config.get('REDIS_PASSWORD', None)

            # Redisが利用できない場合はメモリキャッシュを使用
            self.redis = None
            logger.info("Using in-memory cache")
        except Exception as e:
            self.redis = None
            logger.warning(f"Using in-memory cache: {str(e)}")
        finally:
            self.initialized = True

    def ensure_initialized(self):
        """必要に応じてRedisを初期化"""
        if not self.initialized:
            self._initialize_redis()

    def _serialize(self, value):
        """値をJSON文字列にシリアライズする"""
        if isinstance(value, datetime):
            return value.isoformat()
        return json.dumps(value)

    def _deserialize(self, value):
        """JSON文字列をPythonオブジェクトにデシリアライズする"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def set(self, key, value, expire=None):
        """キャッシュに値を設定する"""
        self.ensure_initialized()
        serialized_value = self._serialize(value)
        if self.redis:
            try:
                if expire:
                    self.redis.setex(key, expire, serialized_value)
                else:
                    self.redis.set(key, serialized_value)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {str(e)}")
                self.fallback_cache[key] = serialized_value
        else:
            self.fallback_cache[key] = serialized_value
        return True

    def get(self, key):
        """キャッシュから値を取得する"""
        self.ensure_initialized()
        if self.redis:
            try:
                value = self.redis.get(key)
                if value:
                    return self._deserialize(value)
            except Exception as e:
                logger.error(f"Redis get error: {str(e)}")
                return self._deserialize(self.fallback_cache.get(key))
        return self._deserialize(self.fallback_cache.get(key))

    def delete(self, key):
        """キャッシュから値を削除する"""
        if self.redis:
            try:
                self.redis.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {str(e)}")
                self.fallback_cache.pop(key, None)
        else:
            self.fallback_cache.pop(key, None)
        return True

    def exists(self, key):
        """キーが存在するかチェックする"""
        if self.redis:
            try:
                return bool(self.redis.exists(key))
            except Exception as e:
                logger.error(f"Redis exists error: {str(e)}")
                return key in self.fallback_cache
        return key in self.fallback_cache

def serialize_message(message):
    """メッセージオブジェクトをシリアライズ可能な形式に変換"""
    return {
        'id': message.id,
        'chat_room_id': message.chat_room_id,
        'sender_id': message.sender_id,
        'recipient_id': message.recipient_id,
        'content': message.content,
        'is_read': message.is_read,
        'created_at': message.created_at.isoformat(),
        'updated_at': message.updated_at.isoformat(),
        'sender': {
            'id': message.sender.id,
            'username': message.sender.username,
            'avatar_url': message.sender.avatar_url if hasattr(message.sender, 'avatar_url') else None
        }
    }

def deserialize_message(data):
    """シリアライズされたメッセージデータを元の形式に戻す"""
    return {
        'id': data['id'],
        'chat_room_id': data['chat_room_id'],
        'sender_id': data['sender_id'],
        'recipient_id': data['recipient_id'],
        'content': data['content'],
        'is_read': data['is_read'],
        'created_at': data['created_at'],
        'updated_at': data['updated_at'],
        'sender': data['sender']
    }

# グローバルキャッシュインスタンス
cache = Cache()

def get_cache_key(room_id, page):
    """キャッシュキーを生成"""
    return f"chat:room:{room_id}:messages:page:{page}"

def cache_messages(room_id, page, messages):
    """メッセージをキャッシュに保存"""
    if not cache.redis:
        return
    
    try:
        cache_key = get_cache_key(room_id, page)
        serialized_messages = [serialize_message(msg) for msg in messages]
        cache.set(cache_key, serialized_messages, CACHE_TTL)
    except Exception as e:
        logger.error(f"Failed to cache messages: {str(e)}")

def get_cached_messages(room_id, page):
    """キャッシュからメッセージを取得"""
    if not cache.redis:
        return None
    
    try:
        cache_key = get_cache_key(room_id, page)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return [deserialize_message(msg) for msg in cached_data]
    except Exception as e:
        logger.error(f"Failed to get cached messages: {str(e)}")
    
    return None

def invalidate_room_cache(room_id):
    """ルームのキャッシュを無効化"""
    if not cache.redis:
        return
    
    try:
        pattern = f"chat:room:{room_id}:messages:page:*"
        keys = cache.redis.keys(pattern)
        if keys:
            cache.delete(*keys)
    except Exception as e:
        logger.error(f"Failed to invalidate room cache: {str(e)}")

def cache_message_status(message_id, is_read):
    """メッセージの既読状態をキャッシュ"""
    if not cache.redis:
        return
    
    try:
        cache_key = f"chat:message:{message_id}:read"
        cache.set(cache_key, str(int(is_read)), CACHE_TTL)
    except Exception as e:
        logger.error(f"Failed to cache message status: {str(e)}")

def get_cached_message_status(message_id):
    """キャッシュからメッセージの既読状態を取得"""
    if not cache.redis:
        return None
    
    try:
        cache_key = f"chat:message:{message_id}:read"
        status = cache.get(cache_key)
        return bool(int(status)) if status is not None else None
    except Exception as e:
        logger.error(f"Failed to get cached message status: {str(e)}")
        return None 