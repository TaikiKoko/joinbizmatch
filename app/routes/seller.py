from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.seller import Seller
from app.forms.seller import SellerRegistrationForm, SellerEditForm
from app import db

bp = Blueprint('seller', __name__)

@bp.route('/seller/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.seller_profile:
        flash('すでに売り手企業として登録されています。', 'warning')
        return redirect(url_for('seller.profile'))

    form = SellerRegistrationForm()
    if form.validate_on_submit():
        seller = Seller(
            user_id=current_user.id,
            company_name=form.company_name.data,
            representative_name=form.representative_name.data,
            establishment_year=form.establishment_year.data,
            capital=form.capital.data,
            employees=form.employees.data,
            annual_sales=form.annual_sales.data,
            business_description=form.business_description.data,
            reason_for_sale=form.reason_for_sale.data,
            desired_successor=form.desired_successor.data,
            asking_price=form.asking_price.data
        )
        db.session.add(seller)
        db.session.commit()
        flash('売り手企業として登録しました。', 'success')
        return redirect(url_for('seller.profile'))

    return render_template('sellers/register.html', form=form)

@bp.route('/seller/profile')
@login_required
def profile():
    if not current_user.seller_profile:
        flash('売り手企業として登録してください。', 'warning')
        return redirect(url_for('seller.register'))
    return render_template('sellers/profile.html', seller=current_user.seller_profile)

@bp.route('/seller/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if not current_user.seller_profile:
        flash('売り手企業として登録してください。', 'warning')
        return redirect(url_for('seller.register'))

    form = SellerEditForm(obj=current_user.seller_profile)
    if form.validate_on_submit():
        current_user.seller_profile.company_name = form.company_name.data
        current_user.seller_profile.representative_name = form.representative_name.data
        current_user.seller_profile.establishment_year = form.establishment_year.data
        current_user.seller_profile.capital = form.capital.data
        current_user.seller_profile.employees = form.employees.data
        current_user.seller_profile.annual_sales = form.annual_sales.data
        current_user.seller_profile.business_description = form.business_description.data
        current_user.seller_profile.reason_for_sale = form.reason_for_sale.data
        current_user.seller_profile.desired_successor = form.desired_successor.data
        current_user.seller_profile.asking_price = form.asking_price.data
        current_user.seller_profile.is_active = form.is_active.data

        db.session.commit()
        flash('企業情報を更新しました。', 'success')
        return redirect(url_for('seller.profile'))

    return render_template('sellers/edit.html', form=form)

@bp.route('/seller/verify/<int:id>', methods=['POST'])
@login_required
def verify_seller(id):
    if not current_user.is_admin:
        return jsonify({'error': '権限がありません。'}), 403

    seller = Seller.query.get_or_404(id)
    seller.is_verified = True
    db.session.commit()
    return jsonify({'message': '企業を認証しました。'})

@bp.route('/seller/deactivate/<int:id>', methods=['POST'])
@login_required
def deactivate_seller(id):
    if not current_user.is_admin:
        return jsonify({'error': '権限がありません。'}), 403

    seller = Seller.query.get_or_404(id)
    seller.is_active = False
    db.session.commit()
    return jsonify({'message': '企業を無効化しました。'}) 