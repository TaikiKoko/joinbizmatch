import os
from werkzeug.utils import secure_filename
from app import db
from app.models.attachment import Attachment
import uuid

ALLOWED_EXTENSIONS = {
    # 画像
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    # 文書
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt',
    # その他
    'zip', 'rar', '7z'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """ファイル拡張子が許可されているかチェック"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_attachment(file, message_id):
    """ファイルを保存し、Attachmentモデルを作成"""
    if not file or not allowed_file(file.filename):
        return None

    if file.content_length > MAX_FILE_SIZE:
        return None

    # ファイル名を安全に処理
    original_filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4()}_{original_filename}"

    # 保存先ディレクトリの作成
    save_dir = os.path.join('app', 'static', 'uploads', 'attachments', str(message_id))
    os.makedirs(save_dir, exist_ok=True)

    # ファイルの保存
    file_path = os.path.join(save_dir, filename)
    file.save(file_path)

    # Attachmentモデルの作成
    attachment = Attachment(
        message_id=message_id,
        filename=filename,
        original_filename=original_filename,
        file_type=file.content_type,
        file_size=file.content_length
    )
    db.session.add(attachment)
    db.session.commit()

    return attachment

def delete_attachment(attachment):
    """ファイルとAttachmentモデルを削除"""
    if attachment:
        # ファイルの削除
        file_path = os.path.join('app', 'static', attachment.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            # ディレクトリが空の場合は削除
            dir_path = os.path.dirname(file_path)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

        # モデルの削除
        db.session.delete(attachment)
        db.session.commit()

def format_file_size(size):
    """ファイルサイズを読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB" 