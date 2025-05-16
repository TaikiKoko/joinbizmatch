from datetime import datetime
from app import db
from app.models.message import Message

class Attachment(db.Model):
    """添付ファイルモデル"""
    __tablename__ = 'attachments'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)  # バイト単位
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    message = db.relationship('Message', backref=db.backref('attachments', lazy=True))

    @property
    def is_image(self):
        """ファイルが画像かどうかを判定"""
        image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        return self.file_type in image_types

    @property
    def icon_class(self):
        """ファイルタイプに応じたアイコンのクラス名を返す"""
        if self.is_image:
            return 'bi-image'
        elif self.file_type == 'application/pdf':
            return 'bi-file-pdf'
        elif 'spreadsheet' in self.file_type or 'excel' in self.file_type:
            return 'bi-file-excel'
        elif 'document' in self.file_type or 'word' in self.file_type:
            return 'bi-file-word'
        else:
            return 'bi-file-earmark'

    def __repr__(self):
        return f'<Attachment {self.original_filename}>' 