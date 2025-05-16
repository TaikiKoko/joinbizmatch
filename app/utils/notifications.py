from app.models.notification import Notification
from app import db

def notify_message(user_id, sender_name, message_preview, chat_url):
    """メッセージ受信時の通知を生成"""
    message = f"{sender_name}さんから新しいメッセージが届きました: {message_preview}"
    return Notification.create_notification(
        user_id=user_id,
        type='message',
        message=message,
        link=chat_url
    )

def notify_favorite(user_id, successor_name, successor_url):
    """お気に入り追加時の通知を生成"""
    message = f"あなたの後継者情報「{successor_name}」がお気に入りに追加されました"
    return Notification.create_notification(
        user_id=user_id,
        type='favorite',
        message=message,
        link=successor_url
    )

def notify_successor_update(user_id, successor_name, successor_url):
    """後継者情報更新時の通知を生成"""
    message = f"後継者情報「{successor_name}」が更新されました"
    return Notification.create_notification(
        user_id=user_id,
        type='successor_update',
        message=message,
        link=successor_url
    )

def notify_successor_created(user_id, successor_name, successor_url):
    """新規後継者情報登録時の通知を生成"""
    message = f"新しい後継者情報「{successor_name}」が登録されました"
    return Notification.create_notification(
        user_id=user_id,
        type='successor_update',
        message=message,
        link=successor_url
    )

def mark_notifications_as_read(user_id):
    """ユーザーの未読通知を既読にマーク"""
    Notification.query.filter_by(
        user_id=user_id,
        read=False
    ).update({'read': True})
    db.session.commit()

def get_unread_count(user_id):
    """ユーザーの未読通知数を取得"""
    return Notification.query.filter_by(
        user_id=user_id,
        read=False
    ).count() 