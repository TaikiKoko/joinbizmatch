from flask import jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Company, Successor
from . import bp as api

@api.route('/favorites/companies/<int:id>', methods=['POST'])
@login_required
def toggle_company_favorite(id):
    if current_user.user_type != 'successor':
        return jsonify({'status': 'error', 'message': '後継者アカウントのみ実行できます'}), 403
    
    company = Company.query.get_or_404(id)
    try:
        if company in current_user.favorite_companies:
            current_user.favorite_companies.remove(company)
            action = 'removed'
        else:
            current_user.favorite_companies.append(company)
            action = 'added'
        db.session.commit()
        return jsonify({'status': 'success', 'action': action})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@api.route('/favorites/successors/<int:id>', methods=['POST'])
@login_required
def toggle_successor_favorite(id):
    if current_user.user_type != 'company':
        return jsonify({'status': 'error', 'message': '企業アカウントのみ実行できます'}), 403
    
    successor = Successor.query.get_or_404(id)
    try:
        if successor in current_user.favorite_successors:
            current_user.favorite_successors.remove(successor)
            action = 'removed'
        else:
            current_user.favorite_successors.append(successor)
            action = 'added'
        db.session.commit()
        return jsonify({'status': 'success', 'action': action})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400 