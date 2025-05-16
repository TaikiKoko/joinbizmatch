from flask import jsonify, request
from app.api import bp
from app.models.company import Company
from app import db

@bp.route('/companies', methods=['GET'])
def get_companies():
    companies = Company.query.all()
    return jsonify([company.to_dict() for company in companies])

@bp.route('/companies/<int:id>', methods=['GET'])
def get_company(id):
    company = Company.query.get_or_404(id)
    return jsonify(company.to_dict())

@bp.route('/companies', methods=['POST'])
def create_company():
    data = request.get_json()
    company = Company(
        user_id=data['user_id'],
        name=data['name'],
        description=data.get('description')
    )
    db.session.add(company)
    db.session.commit()
    return jsonify(company.to_dict()), 201

@bp.route('/companies/<int:id>', methods=['PUT'])
def update_company(id):
    company = Company.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data:
        company.name = data['name']
    if 'description' in data:
        company.description = data['description']
    db.session.commit()
    return jsonify(company.to_dict()) 