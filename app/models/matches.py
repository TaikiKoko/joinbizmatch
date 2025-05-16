from datetime import datetime
from app import db

class CompanySuccessorMatch(db.Model):
    __tablename__ = 'company_successor_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    successor_id = db.Column(db.Integer, db.ForeignKey('successors.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    company = db.relationship('Company', back_populates='matches')
    successor = db.relationship('Successor', back_populates='matches')
    
    def __repr__(self):
        return f'<Match {self.company_id} - {self.successor_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'successor_id': self.successor_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 