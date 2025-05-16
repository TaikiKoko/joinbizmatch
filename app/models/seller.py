from datetime import datetime
from app import db

class Seller(db.Model):
    __tablename__ = 'sellers'
    __table_args__ = (
        {'extend_existing': True},
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    representative_name = db.Column(db.String(100), nullable=False)
    establishment_year = db.Column(db.Integer, nullable=False)
    capital = db.Column(db.Integer)  # 資本金
    employees = db.Column(db.Integer)  # 従業員数
    annual_sales = db.Column(db.Integer)  # 年間売上
    business_description = db.Column(db.Text)  # 事業内容
    reason_for_sale = db.Column(db.Text)  # 売却理由
    desired_successor = db.Column(db.Text)  # 希望する後継者像
    asking_price = db.Column(db.Integer)  # 希望価格
    is_verified = db.Column(db.Boolean, default=False)  # 認証済みかどうか
    is_active = db.Column(db.Boolean, default=True)  # アクティブかどうか
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    user = db.relationship('User', backref=db.backref('seller', uselist=False))

    def __init__(self, user_id, name, company_name, position, phone):
        self.user_id = user_id
        self.name = name
        self.company_name = company_name
        self.position = position
        self.phone = phone

    def __repr__(self):
        return f'<Seller {self.company_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'company_name': self.company_name,
            'position': self.position,
            'phone': self.phone,
            'representative_name': self.representative_name,
            'establishment_year': self.establishment_year,
            'capital': self.capital,
            'employees': self.employees,
            'annual_sales': self.annual_sales,
            'business_description': self.business_description,
            'reason_for_sale': self.reason_for_sale,
            'desired_successor': self.desired_successor,
            'asking_price': self.asking_price,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 