from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.profile import bp
from app.profile.forms import CompanyProfileForm, SuccessorProfileForm
from app.models.company import Company
from app.models.successor import Successor
from app.models.user import User
import sqlalchemy
import traceback

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/company/setup', methods=['GET', 'POST'])
@login_required
def setup_company():
    try:
        # 企業ユーザーでない場合のチェック
        if current_user.user_type != 'company':
            flash('企業アカウントでログインしてください。', 'warning')
            return redirect(url_for('auth.login_company'))
        
        current_app.logger.info("=== Setup Company Debug ===")
        current_app.logger.info(f"User ID: {current_user.id}")
        current_app.logger.info(f"Request Method: {request.method}")
        
        # companyオブジェクトが存在しない場合は作成
        if not current_user.company:
            try:
                company = Company(user_id=current_user.id)
                db.session.add(company)
                db.session.commit()
                current_user.company = company
                current_app.logger.info("Created new company profile")
            except Exception as e:
                current_app.logger.error(f"企業プロフィール作成エラー: {str(e)}")
                db.session.rollback()
                flash('プロフィールの作成に失敗しました。', 'danger')
                return redirect(url_for('auth.login_company'))
        
        form = CompanyProfileForm()
        
        # デバッグ情報の追加
        if request.method == 'POST':
            current_app.logger.info('POST request received')
            current_app.logger.info(f'Form data: {request.form}')
            current_app.logger.info(f'Form errors: {form.errors}')
            current_app.logger.info(f'Form validation status: {form.validate()}')
        
        # 編集モードの判定
        is_edit = request.args.get('edit') == 'true'
        current_app.logger.info(f"Edit mode: {is_edit}")
        
        # 編集モードでない場合のみプロフィール完了チェックを行う
        if not is_edit and current_user.has_completed_profile():
            flash('プロフィールは既に設定済みです。', 'info')
            return redirect(url_for('profile.view_company_profile', id=current_user.company.id))
        
        if form.validate_on_submit():
            try:
                current_app.logger.info("Form validated, updating profile...")
                
                # プロフィール情報の更新前の状態をログ
                current_app.logger.info("Current profile state:")
                current_app.logger.info(f"Name: {current_user.company.name}")
                current_app.logger.info(f"Revenue: {current_user.company.annual_revenue}")
                current_app.logger.info(f"Profit: {current_user.company.operating_profit}")
                
                # プロフィール画像のアップロード
                if form.company_images.data:
                    file = form.company_images.data
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_images', 'company', filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        file.save(file_path)
                        current_user.company.image_path = f'profile_images/company/{filename}'
                        current_user.avatar_url = f'static/uploads/profile_images/company/{filename}'
                
                # プロフィール情報の更新
                current_user.company.name = form.company_name.data
                current_user.company.industry = form.industry.data
                current_user.company.location = form.location.data
                current_user.company.employee_count = form.employee_count.data
                current_user.company.established_year = form.established_year.data
                current_user.company.annual_revenue = form.annual_revenue.data
                current_user.company.operating_profit = form.operating_profit.data
                current_user.company.capital = form.capital.data
                current_user.company.business_description = form.business_description.data
                current_user.company.short_description = form.short_description.data
                current_user.company.succession_reason = form.succession_reason.data
                current_user.company.desired_conditions = form.desired_conditions.data
                
                # 更新後の状態をログ
                current_app.logger.info("Updated profile state:")
                current_app.logger.info(f"Name: {current_user.company.name}")
                current_app.logger.info(f"Revenue: {current_user.company.annual_revenue}")
                current_app.logger.info(f"Profit: {current_user.company.operating_profit}")
                
                # プロフィール完了状態を更新
                is_completed = current_user.company.update_profile_completed_status()
                
                # データベースに保存
                db.session.commit()
                current_app.logger.info("Profile successfully updated and committed to database")
                
                if is_completed:
                    flash('プロフィールを設定しました。', 'success')
                    return redirect(url_for('profile.confirm_company_profile'))
                else:
                    flash('必須項目をすべて入力してください。', 'warning')
                    return render_template('profile/company/setup.html',
                                        title='企業プロフィール設定',
                                        form=form,
                                        is_edit=is_edit)
                
            except Exception as e:
                current_app.logger.error(f"プロフィール更新エラー: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                db.session.rollback()
                
                if isinstance(e, sqlalchemy.exc.IntegrityError):
                    flash('入力された情報が重複しているか、必須項目が不足しています。', 'danger')
                elif isinstance(e, sqlalchemy.exc.DataError):
                    flash('入力された値が適切な範囲を超えています。', 'danger')
                else:
                    flash('プロフィールの更新に失敗しました。', 'danger')
                
                return render_template('profile/company/setup.html',
                                    title='企業プロフィール設定',
                                    form=form,
                                    is_edit=is_edit)
        
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{form[field].label.text}: {error}', 'danger')
        
        # GETリクエストまたはバリデーションエラーの場合、既存のデータがあれば表示
        if request.method == 'GET' and current_user.company:
            current_app.logger.info("Loading existing profile data into form")
            form.company_name.data = current_user.company.name
            form.industry.data = current_user.company.industry
            form.location.data = current_user.company.location
            form.employee_count.data = current_user.company.employee_count
            form.established_year.data = current_user.company.established_year
            form.annual_revenue.data = current_user.company.annual_revenue
            form.operating_profit.data = current_user.company.operating_profit
            form.capital.data = current_user.company.capital
            form.business_description.data = current_user.company.business_description
            form.short_description.data = current_user.company.short_description
            form.succession_reason.data = current_user.company.succession_reason
            form.desired_conditions.data = current_user.company.desired_conditions
        
        return render_template('profile/company/setup.html',
                             title='企業プロフィール設定',
                             form=form,
                             is_edit=is_edit)
    except Exception as e:
        current_app.logger.error(f"Unexpected error in setup_company: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        raise

@bp.route('/company/<int:id>')
def view_company_profile(id):
    """企業プロフィール表示"""
    # セッションをリフレッシュして最新のデータを取得
    db.session.expire_all()
    
    company = Company.query.get_or_404(id)
    is_own_profile = current_user.is_authenticated and current_user.user_type == 'company' and current_user.company.id == company.id
    
    return render_template('profile/company/view.html',
                         title=f'{company.name}のプロフィール',
                         company=company,
                         is_own_profile=is_own_profile)

@bp.route('/company/confirm', methods=['GET', 'POST'])
@login_required
def confirm_company_profile():
    if current_user.user_type != 'company':
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # プロフィール確認完了、プロフィール表示画面へ
        flash('プロフィール設定が完了しました。', 'success')
        return redirect(url_for('profile.view_company_profile', id=current_user.company.id))
    
    # GETリクエストの場合は確認画面を表示
    return render_template('profile/company/confirm.html',
                         title='プロフィール確認',
                         company=current_user.company)

@bp.route('/successor/setup', methods=['GET', 'POST'])
@login_required
def setup_successor():
    """後継者プロフィール設定"""
    if current_user.user_type != 'successor':
        flash('このページにはアクセスできません。', 'warning')
        return redirect(url_for('auth.login_successor'))

    successor = Successor.query.filter_by(user_id=current_user.id).first()
    
    # 新規作成の場合
    if not successor:
        successor = Successor(user_id=current_user.id)
        db.session.add(successor)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"新規プロフィール作成エラー: {str(e)}")
            flash('プロフィールの作成に失敗しました。', 'danger')
            return redirect(url_for('main.index'))

    form = SuccessorProfileForm()
    if form.validate_on_submit():
        try:
            # 必須項目のバリデーション
            if form.gender.data == '未設定':
                flash('性別を選択してください。', 'danger')
                return render_template('profile/successor/setup.html', 
                                    title='後継者プロフィール設定',
                                    form=form,
                                    is_edit=successor is not None and successor.is_profile_completed)

            if form.location.data == '未設定':
                flash('現在の所在地を選択してください。', 'danger')
                return render_template('profile/successor/setup.html', 
                                    title='後継者プロフィール設定',
                                    form=form,
                                    is_edit=successor is not None and successor.is_profile_completed)

            if form.desired_industry.data == 'none':
                flash('希望業界を選択してください。', 'danger')
                return render_template('profile/successor/setup.html', 
                                    title='後継者プロフィール設定',
                                    form=form,
                                    is_edit=successor is not None and successor.is_profile_completed)

            if form.desired_location.data == '未設定':
                flash('希望地域を選択してください。', 'danger')
                return render_template('profile/successor/setup.html', 
                                    title='後継者プロフィール設定',
                                    form=form,
                                    is_edit=successor is not None and successor.is_profile_completed)

            if form.investment_capacity.data == '未設定':
                flash('投資可能額を選択してください。', 'danger')
                return render_template('profile/successor/setup.html', 
                                    title='後継者プロフィール設定',
                                    form=form,
                                    is_edit=successor is not None and successor.is_profile_completed)

            # 基本情報の更新
            successor.name = form.name.data
            successor.age = form.age.data
            successor.gender = form.gender.data
            successor.location = form.location.data
            successor.description = form.description.data

            # 希望条件の更新
            successor.desired_industry = form.desired_industry.data
            successor.desired_location = form.desired_location.data
            successor.investment_capacity = form.investment_capacity.data

            # 経験の更新
            successor.management_experience = form.management_experience.data
            successor.industry_experience = form.industry_experience.data

            # プロフィール画像の処理
            if form.images.data:
                file = form.images.data
                if file and allowed_file(file.filename):
                    try:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_images', 'successor', filename)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        file.save(file_path)
                        successor.image_filename = f'profile_images/successor/{filename}'
                        # 必要に応じてUser.avatar_urlも更新
                        if successor.user:
                            successor.user.avatar_url = f'static/uploads/profile_images/successor/{filename}'
                    except Exception as e:
                        current_app.logger.error(f"画像アップロードエラー: {str(e)}")
                        flash('画像のアップロードに失敗しました。', 'danger')

            # 公開設定の更新
            successor.is_public = form.is_public.data

            # プロフィール完了状態の確認
            is_completed = successor.is_profile_completed
            
            # データベースに保存
            db.session.commit()

            if is_completed:
                flash('プロフィールを更新しました。', 'success')
                return redirect(url_for('profile.view_successor_profile', id=successor.id))
            else:
                flash('必須項目をすべて入力してください。', 'warning')
                
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"プロフィール更新エラー: {str(e)}")
            flash('プロフィールの更新に失敗しました。', 'danger')
    
    elif request.method == 'GET':
        # 既存のデータがある場合はフォームに設定
        if successor:
            form.name.data = successor.name
            form.age.data = successor.age
            form.gender.data = successor.gender
            form.location.data = successor.location
            form.description.data = successor.description
            form.desired_industry.data = successor.desired_industry
            form.desired_location.data = successor.desired_location
            form.investment_capacity.data = successor.investment_capacity
            form.management_experience.data = successor.management_experience
            form.industry_experience.data = successor.industry_experience
            form.is_public.data = successor.is_public

    # バリデーションエラーの表示
    if form.errors:
        for field, errors in form.errors.items():
            error_messages = []
            for error in errors:
                error_messages.append(f"{getattr(form, field).label.text}: {error}")
            flash("・" + "\n・".join(error_messages), 'danger')

    return render_template('profile/successor/setup.html', 
                         title='後継者プロフィール設定',
                         form=form,
                         is_edit=successor is not None and successor.is_profile_completed)

@bp.route('/company/edit', methods=['GET', 'POST'])
@login_required
def edit_company_profile():
    if current_user.user_type != 'company':
        flash('企業アカウントでログインしてください。', 'danger')
        return redirect(url_for('main.index'))

    form = CompanyProfileForm()
    
    if form.validate_on_submit():
        current_user.company.name = form.company_name.data
        current_user.company.industry = form.industry.data
        current_user.company.location = form.location.data
        current_user.company.employee_count = form.employee_count.data
        current_user.company.established_year = form.established_year.data
        current_user.company.annual_revenue = form.annual_revenue.data
        current_user.company.operating_profit = form.operating_profit.data
        current_user.company.capital = form.capital.data
        current_user.company.business_description = form.business_description.data
        current_user.company.short_description = form.short_description.data
        current_user.company.succession_reason = form.succession_reason.data
        current_user.company.desired_conditions = form.desired_conditions.data

        if form.company_images.data:
            file = form.company_images.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_images', 'company', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                current_user.company.image_path = f'profile_images/company/{filename}'
                current_user.avatar_url = f'static/uploads/profile_images/company/{filename}'

        db.session.commit()
        flash('プロフィールを更新しました。', 'success')
        return redirect(url_for('profile.view_company_profile', id=current_user.company.id))

    elif request.method == 'GET':
        form.company_name.data = current_user.company.name
        form.industry.data = current_user.company.industry
        form.location.data = current_user.company.location
        form.employee_count.data = current_user.company.employee_count
        form.established_year.data = current_user.company.established_year
        form.annual_revenue.data = current_user.company.annual_revenue
        form.operating_profit.data = current_user.company.operating_profit
        form.capital.data = current_user.company.capital
        form.business_description.data = current_user.company.business_description
        form.short_description.data = current_user.company.short_description
        form.succession_reason.data = current_user.company.succession_reason
        form.desired_conditions.data = current_user.company.desired_conditions

    return render_template('profile/company/setup.html',
                         title='企業プロフィール編集',
                         form=form,
                         is_edit=True)

@bp.route('/successor/edit', methods=['GET', 'POST'])
@login_required
def edit_successor_profile():
    return redirect(url_for('profile.setup_successor'))

@bp.route('/successor/profile', methods=['GET', 'POST'])
@login_required
def successor_profile():
    # Get or create successor profile
    successor = Successor.query.filter_by(user_id=current_user.id).first()
    if not successor:
        successor = Successor(user_id=current_user.id)
        db.session.add(successor)
        db.session.commit()

    form = SuccessorProfileForm(obj=successor)
    
    if form.validate_on_submit():
        form.populate_obj(successor)
        db.session.commit()
        flash('プロフィールを更新しました。', 'success')
        return redirect(url_for('profile.successor_profile'))
        
    return render_template('profile/successor/profile.html', 
                         title='後継者プロフィール',
                         form=form,
                         successor=successor)

@bp.route('/successor/view/<int:id>', methods=['GET', 'POST'])
def view_successor_profile(id):
    successor = Successor.query.get_or_404(id)
    
    # 自分のプロフィールかどうかをチェック
    is_own_profile = current_user.is_authenticated and successor.user_id == current_user.id
    
    # POSTリクエストの処理（自分のプロフィールの場合のみ）
    if request.method == 'POST' and is_own_profile:
        try:
            # プロフィール完了フラグを設定
            successor.is_profile_completed = True
            db.session.commit()
            flash('プロフィールの設定が完了しました。', 'success')
            return redirect(url_for('main.successor_mypage'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"プロフィール確認エラー: {str(e)}")
            flash('プロフィールの確認に失敗しました。', 'danger')
            return redirect(url_for('profile.setup_successor'))

    # プロフィールが非公開で、自分のプロフィールでない場合
    if not successor.is_public and not is_own_profile:
        flash('このプロフィールは非公開です。', 'warning')
        return redirect(url_for('main.index'))

    return render_template('profile/successor/view.html',
                         title=f'{successor.name}のプロフィール',
                         successor=successor,
                         is_own_profile=is_own_profile)

@bp.route('/successor/confirm/<int:id>', methods=['POST'])
@login_required
def confirm_successor_profile(id):
    """後継者プロフィールの確認完了"""
    successor = Successor.query.get_or_404(id)
    
    # 権限チェック
    if successor.user_id != current_user.id:
        flash('この操作は許可されていません。', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        if successor.is_profile_completed:
            flash('プロフィールの設定が完了しました。', 'success')
            return redirect(url_for('main.successor_mypage'))
        else:
            flash('プロフィールの入力内容を確認してください。', 'warning')
            return redirect(url_for('profile.setup_successor'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"プロフィール確認エラー: {str(e)}")
        flash('プロフィールの確認に失敗しました。', 'danger')
        return redirect(url_for('profile.setup_successor')) 