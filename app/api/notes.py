from flask import jsonify, request
from app.api import bp
from app.models.note import Note
from app import db

@bp.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes])

@bp.route('/notes/<int:id>', methods=['GET'])
def get_note(id):
    note = Note.query.get_or_404(id)
    return jsonify(note.to_dict())

@bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    note = Note(
        user_id=data['user_id'],
        title=data['title'],
        content=data['content']
    )
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

@bp.route('/notes/<int:id>', methods=['PUT'])
def update_note(id):
    note = Note.query.get_or_404(id)
    data = request.get_json()
    if 'title' in data:
        note.title = data['title']
    if 'content' in data:
        note.content = data['content']
    db.session.commit()
    return jsonify(note.to_dict()) 