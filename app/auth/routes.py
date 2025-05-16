from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, CompanyRegistrationForm, SuccessorRegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models.user import User
from app.auth.mail_utils import send_password_reset_email
from datetime import datetime
from app.models.company import Company
from app.models.successor import Successor
from werkzeug.urls import url_parse

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('メールアドレスまたはパスワードが正しくありません。', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='ログイン', form=form)

@bp.route('/login_redirect')
def login_redirect():
    """ユーザータイプに応じて適切なログインページにリダイレクト"""
    next_page = request.args.get('next')
    if current_user.is_authenticated:
        if current_user.user_type == 'company':
            return redirect(url_for('auth.login_company'))
        else:
            return redirect(url_for('auth.login_successor'))
    elif next_page and 'company' in next_page:
        return redirect(url_for('auth.login_company'))
    else:
        return redirect(url_for('auth.login_successor'))

@bp.route('/company/login', methods=['GET', 'POST'])
def login_company():
    if current_user.is_authenticated:
        return redirect(url_for('main.company_mypage'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, user_type='company').first()
        
        if user is None:
            flash('メールアドレスが見つかりません。', 'danger')
            return render_template('auth/login_company.html', title='企業ログイン', form=form)
            
        if not user.check_password(form.password.data):
            flash('パスワードが正しくありません。', 'danger')
            return render_template('auth/login_company.html', title='企業ログイン', form=form)
        
        login_user(user, remember=form.remember_me.data)
        
        # プロフィール設定状態をチェック
        company = Company.query.filter_by(user_id=user.id).first()
        if not company or not company.is_profile_completed:
            return redirect(url_for('profile.setup_company'))
        
        next_page = request.args.get('next')
        if next_page and urlparse(next_page).netloc == '':
            return redirect(next_page)
        return redirect(url_for('main.company_mypage'))
    
    return render_template('auth/login_company.html', title='企業ログイン', form=form)

@bp.route('/successor/login', methods=['GET', 'POST'])
def login_successor():
    """後継者用ログインルート"""
    if current_user.is_authenticated:
        successor = Successor.query.filter_by(user_id=current_user.id).first()
        if not successor or not successor.is_profile_completed:
            return redirect(url_for('profile.setup_successor'))
        return redirect(url_for('main.mypage'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, user_type='successor').first()
        if user is None:
            flash('このメールアドレスは登録されていません。新規登録してください。', 'danger')
            return redirect(url_for('auth.register_successor'))
        if not user.check_password(form.password.data):
            flash('パスワードが正しくありません。', 'danger')
            return render_template('auth/login_successor.html', title='後継者ログイン', form=form)
        
        login_user(user, remember=form.remember_me.data)
        
        # プロフィール設定状態をチェック
        successor = Successor.query.filter_by(user_id=user.id).first()
        if not successor or not successor.is_profile_completed:
            return redirect(url_for('profile.setup_successor'))
        
        next_page = request.args.get('next')
        if next_page and urlparse(next_page).netloc == '':
            return redirect(next_page)
        
        return redirect(url_for('main.mypage'))
    
    return render_template('auth/login_successor.html', title='後継者ログイン', form=form)

@bp.route('/company/register', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        # 既にログインしている場合は、強制的にログアウト
        logout_user()
    
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        try:
            # メールアドレスの@より前の部分をユーザー名として使用
            username = form.email.data.split('@')[0]
            
            user = User(
                username=username,
                email=form.email.data,
                user_type='company'
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            
            company = Company(user_id=user.id, name="未設定")
            db.session.add(company)
            db.session.commit()
            
            flash('企業アカウントの登録が完了しました。ログインしてプロフィールを設定してください。', 'success')
            return redirect(url_for('auth.login_company'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"企業登録エラー: {str(e)}")
            flash('登録中にエラーが発生しました。もう一度お試しください。', 'danger')
            return redirect(url_for('auth.register_company'))
    
    return render_template('auth/register_company.html', title='企業新規登録', form=form, current_year=datetime.now().year)

@bp.route('/successor/register', methods=['GET', 'POST'])
def register_successor():
    if current_user.is_authenticated:
        return redirect(url_for('main.mypage'))
    
    form = SuccessorRegistrationForm()
    if form.validate_on_submit():
        try:
            # メールアドレスの@より前の部分をユーザー名として使用
            username = form.email.data.split('@')[0]
            
            # ユーザーの作成
            user = User(
                username=username,
                email=form.email.data,
                user_type='successor'
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # IDを生成するためにflush
            
            # 後継者プロフィールの作成（必須フィールドを適切に設定）
            successor = Successor(
                user_id=user.id,
                name="未設定",
                description="",
                industry="none",  # 初期値を設定
                location="未設定"
            )
            successor.age = None
            successor.gender = "未設定"
            successor.desired_industry = "none"
            successor.desired_location = "未設定"
            successor.investment_capacity = "未設定"
            successor.management_experience = ""
            successor.industry_experience = ""
            successor.is_public = True
            
            db.session.add(successor)
            db.session.commit()
            
            flash('後継者アカウントの登録が完了しました。ログインしてプロフィールを設定してください。', 'success')
            return redirect(url_for('auth.login_successor'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"後継者登録エラー: {str(e)}")
            flash('登録中にエラーが発生しました。もう一度お試しください。', 'danger')
            return redirect(url_for('auth.register_successor'))
    
    return render_template('auth/register_successor.html', title='後継者新規登録', form=form, current_year=datetime.now().year)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return login_redirect()
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash('パスワードリセット手順をメールで送信しました。', 'info')
            return redirect(url_for('auth.login_company' if user.user_type == 'company' else 'auth.login_successor'))
    
    return render_template('auth/reset_password_request.html',
                         title='パスワードリセット', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return login_redirect()
    
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('パスワードが更新されました。', 'success')
        return redirect(url_for('auth.login_company' if user.user_type == 'company' else 'auth.login_successor'))
    
    return render_template('auth/reset_password.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('登録が完了しました。', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='新規登録', form=form) 