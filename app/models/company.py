from datetime import datetime
from app import db
from app.models.matches import CompanySuccessorMatch
from app.models.tables import company_favorites
from sqlalchemy import CheckConstraint

class Company(db.Model):
    """企業モデル"""
    __tablename__ = 'companies'
    __table_args__ = (
        CheckConstraint(
            "industry IN ('none', 'manufacturing', 'retail', 'service', 'it', 'construction', 'food', 'real_estate', 'medical', 'education', 'agriculture', 'other')",
            name='check_industry_values'
        ),
        {'extend_existing': True}
    )

    # 業種の日本語変換辞書
    INDUSTRY_LABELS = {
        'none': '特になし',
        'manufacturing': '製造業',
        'retail': '小売業',
        'service': 'サービス業',
        'it': 'IT・通信',
        'construction': '建設業',
        'food': '飲食業',
        'real_estate': '不動産業',
        'medical': '医療・福祉',
        'education': '教育',
        'agriculture': '農林水産業',
        'other': 'その他'
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    employee_count = db.Column(db.Integer)
    established_year = db.Column(db.Integer)
    annual_revenue = db.Column(db.Integer, doc='年間売上（万円）')  # 万円
    operating_profit = db.Column(db.Integer, doc='営業利益（万円）')  # 万円
    capital = db.Column(db.Integer, doc='資本金（万円）')  # 万円
    business_description = db.Column(db.Text)
    succession_reason = db.Column(db.Text)
    desired_conditions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_profile_completed = db.Column(db.Boolean, default=False)
    image_path = db.Column(db.String(200), nullable=True)  # 画像パス
    short_description = db.Column(db.String(200), nullable=True)  # カード用ショートメッセージ
    homepage = db.Column(db.String(200), nullable=True)  # ホームページ
    instagram = db.Column(db.String(200), nullable=True)  # インスタグラム
    twitter = db.Column(db.String(200), nullable=True)  # ツイッター

    # リレーションシップ
    user = db.relationship('User', back_populates='company')
    matches = db.relationship('CompanySuccessorMatch', back_populates='company')
    favorited_by = db.relationship('User',
                                  secondary=company_favorites,
                                  lazy='dynamic',
                                  back_populates='favorite_companies')

    def __init__(self, user_id, name, description=None, industry=None, location=None, website=None):
        self.user_id = user_id
        self.name = name
        self.description = description
        self.industry = industry
        self.location = location
        self.website = website
        self.is_profile_completed = False

    def to_dict(self):
        """APIレスポンス用の辞書を返す"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'industry': self.industry,
            'industry_label': self.industry_label,
            'location': self.location,
            'website': self.website,
            'employee_count': self.employee_count,
            'established_year': self.established_year,
            'annual_revenue': self.annual_revenue,
            'operating_profit': self.operating_profit,
            'capital': self.capital,
            'business_description': self.business_description,
            'succession_reason': self.succession_reason,
            'desired_conditions': self.desired_conditions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_profile_completed': self.is_profile_completed,
            'image_path': self.image_path,
            'short_description': self.short_description,
            'homepage': self.homepage,
            'instagram': self.instagram,
            'twitter': self.twitter
        }

    def __repr__(self):
        return f'<Company {self.name}>'

    def check_profile_completed(self):
        """プロフィールが完了しているかどうかを判定"""
        required_fields = [
            bool(self.name and self.name != "未設定"),
            bool(self.industry),
            bool(self.location),
            bool(self.employee_count),
            bool(self.established_year),
            bool(self.annual_revenue),
            bool(self.operating_profit),
            bool(self.capital),
            bool(self.business_description and len(self.business_description.strip()) > 0),
            bool(self.succession_reason and len(self.succession_reason.strip()) > 0),
            bool(self.desired_conditions and len(self.desired_conditions.strip()) > 0)
        ]
        return all(required_fields)

    def update_profile_completed_status(self):
        """プロフィール完了状態を更新"""
        self.is_profile_completed = self.check_profile_completed()
        return self.is_profile_completed

    @property
    def industry_label(self):
        """業種の日本語表示を返す"""
        return self.INDUSTRY_LABELS.get(self.industry, '未設定') 