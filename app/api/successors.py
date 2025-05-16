from flask import jsonify, request
from app.api import bp
from app.models.successor import Successor
from app import db

@bp.route('/successors', methods=['GET'])
def get_successors():
    successors = Successor.query.all()
    return jsonify([successor.to_dict() for successor in successors])

@bp.route('/successors/<int:id>', methods=['GET'])
def get_successor(id):
    successor = Successor.query.get_or_404(id)
    return jsonify(successor.to_dict())

@bp.route('/successors', methods=['POST'])
def create_successor():
    data = request.get_json()
    successor = Successor(
        user_id=data['user_id'],
        name=data['name'],
        description=data.get('description')
    )
    db.session.add(successor)
    db.session.commit()
    return jsonify(successor.to_dict()), 201

@bp.route('/successors/<int:id>', methods=['PUT'])
def update_successor(id):
    successor = Successor.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data:
        successor.name = data['name']
    if 'description' in data:
        successor.description = data['description']
    db.session.commit()
    return jsonify(successor.to_dict()) 