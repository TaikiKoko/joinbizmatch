from datetime import datetime
from app import db
from app.models.matches import CompanySuccessorMatch
from app.models.tables import successor_favorites # インポート元を変更

class Successor(db.Model):
    """後継者モデル"""
    __tablename__ = 'successors'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Basic Information
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Desired Conditions
    desired_industry = db.Column(db.String(20))
    desired_location = db.Column(db.String(20))
    investment_capacity = db.Column(db.String(50))
    
    # Experience
    management_experience = db.Column(db.Text)
    industry_experience = db.Column(db.Text)
    
    # Privacy Settings
    is_public = db.Column(db.Boolean, default=True)
    
    # Profile Image
    image_filename = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='successor')
    matches = db.relationship('CompanySuccessorMatch', back_populates='successor')
    favorited_by = db.relationship('User',
                                  secondary=successor_favorites,
                                  lazy='dynamic',
                                  back_populates='favorite_successors')

    def __init__(self, user_id, name="未設定", description=None, industry=None, location=None):
        self.user_id = user_id
        self.name = name
        self.description = description
        self.desired_industry = industry
        self.location = location
        self.is_public = True  # デフォルトで公開
        self.age = None
        self.gender = "未設定"
        self.desired_location = "未設定"
        self.investment_capacity = "未設定"
        self.management_experience = ""
        self.industry_experience = ""

    def to_dict(self):
        """APIレスポンス用の辞書を返す"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'location': self.location,
            'description': self.description,
            'desired_industry': self.desired_industry,
            'desired_location': self.desired_location,
            'investment_capacity': self.investment_capacity,
            'management_experience': self.management_experience,
            'industry_experience': self.industry_experience,
            'is_public': self.is_public,
            'image_filename': self.image_filename,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Successor {self.name}>'

    @property
    def is_profile_completed(self):
        """プロフィールが完了しているかどうかを判定します"""
        required_fields = [
            bool(self.name and self.name != "未設定"),  # 名前は必須
            bool(self.gender and self.gender != "未設定"),  # 性別は必須
            bool(self.location and self.location != "未設定"),  # 所在地は必須
            bool(self.desired_industry and self.desired_industry != "none"),  # 希望業界は必須
            bool(self.desired_location and self.desired_location != "未設定"),  # 希望地域は必須
            bool(self.investment_capacity and self.investment_capacity != "未設定"),  # 投資可能額は必須
        ]
        
        # 年齢は入力された場合のみ検証
        if self.age is not None:
            required_fields.append(isinstance(self.age, int) and 18 <= self.age <= 100)
            
        # 説明文は入力された場合のみ長さを検証
        if self.description:
            required_fields.append(len(self.description.strip()) > 0)
            
        # 経験は入力された場合のみ長さを検証
        if self.management_experience:
            required_fields.append(len(self.management_experience.strip()) > 0)
        if self.industry_experience:
            required_fields.append(len(self.industry_experience.strip()) > 0)
            
        return all(required_fields)

    def update_profile_completed_status(self):
        """プロフィール完了状態を更新"""
        return self.is_profile_completed 