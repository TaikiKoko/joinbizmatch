from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, session
from flask_login import login_required, current_user, logout_user
from app import db
from app.main import bp
from app.models.user import User
from app.models.company import Company
from app.models.successor import Successor
from app.models.chat_room import ChatRoom
from app.models.message import Message
from app.models.notification import Notification
from app.models.note import Note
from app.models.matches import CompanySuccessorMatch
from datetime import datetime
from app.forms.contact_form import ContactForm
from app.models.seller import Seller
from flask import current_app
import traceback
import sys
import json
from app.utils.choices import INDUSTRY_CHOICES, LOCATION_CHOICES
from sqlalchemy import and_
from app.models.blocked_user import BlockedUser
from app.forms.settings import ChangeEmailForm, ChangePasswordForm, DeactivateAccountForm
from werkzeug.urls import url_parse
from app.utils.email_verification import create_verification_record, verify_token
import os
from app.main.forms import ContactForm, NoteForm, CompanySearchForm
from app.models import Contact
from app.utils.email import send_contact_confirmation, send_contact_notification, send_email
from app.models.announcement import Announcement

# 管理者チェック用デコレータ
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('管理者のみアクセス可能です。')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
def index():
    return render_template('main/index.html', title='ホーム')

@bp.route('/mypage')
@login_required
def mypage():
    # 既存の/mypageへのアクセスを新しいURLにリダイレクト
    if current_user.user_type == 'company':
        return redirect(url_for('main.company_mypage'))
    else:
        return redirect(url_for('main.successor_mypage'))

@bp.route('/company/mypage')
@login_required
def company_mypage():
    if current_user.user_type != 'company':
        return redirect(url_for('main.successor_mypage'))
    
    # 企業情報が存在しない場合は設定ページへ
    if not current_user.company:
        return redirect(url_for('profile.setup_company'))
    
    # プロフィールが未完了の場合は設定ページへ
    if not current_user.company.is_profile_completed:
        return redirect(url_for('profile.setup_company'))
    
    # 未読メッセージ数を取得
    unread_messages_count = Message.query.join(ChatRoom).filter(
        ((ChatRoom.user1_id == current_user.id) | (ChatRoom.user2_id == current_user.id)),
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).count()
    
    # 未読の通知数を取得
    unread_notifications_count = Notification.query.filter_by(
        user_id=current_user.id,
        read=False
    ).count()
    
    return render_template('main/company_mypage.html',
                        title='企業マイページ',
                        user=current_user,
                        company=current_user.company,
                        unread_messages_count=unread_messages_count,
                        unread_notifications_count=unread_notifications_count)

@bp.route('/successor/mypage')
@login_required
def successor_mypage():
    print("=== Successor Mypage Debug ===")
    print(f"Current user: {current_user}")
    print(f"User type: {current_user.user_type}")
    print(f"User ID: {current_user.id}")
    
    if current_user.user_type != 'successor':
        return redirect(url_for('main.company_mypage'))
    
    if not current_user.has_completed_profile():
        print("Profile not completed")
        return redirect(url_for('profile.setup_successor'))
    
    # 最新のメッセージ
    messages = Message.query.join(ChatRoom).filter(
        ((ChatRoom.user1_id == current_user.id) | (ChatRoom.user2_id == current_user.id))
    ).order_by(Message.created_at.desc()).limit(5).all()
    
    # 未読の通知
    notifications = current_user.notifications.filter_by(read=False).order_by(Notification.created_at.desc()).all()
    
    # お気に入りの企業を取得
    favorite_companies = current_user.favorite_companies.all()
    
    # ブロックされた企業を取得
    blocked_companies = Company.query.join(
        User, Company.user_id == User.id
    ).join(
        BlockedUser,
        (BlockedUser.blocked_id == User.id) & 
        (BlockedUser.blocker_id == current_user.id)
    ).all()
    
    # 未読メッセージ数を計算
    unread_messages_count = Message.query.join(ChatRoom).filter(
        ((ChatRoom.user1_id == current_user.id) | (ChatRoom.user2_id == current_user.id)),
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).count()
    
    print("=== Rendering Successor Mypage ===")
    print(f"Successor object: {current_user.successor}")
    print(f"Successor name: {current_user.successor.name if current_user.successor else 'No name'}")
    print(f"Favorite companies count: {len(favorite_companies)}")
    print(f"Blocked companies count: {len(blocked_companies)}")
    
    return render_template('main/successor_mypage.html',
                        title='後継者マイページ',
                        user=current_user,
                        successor=current_user.successor,
                        messages=messages,
                        notifications=notifications,
                        favorite_companies=favorite_companies,
                        blocked_companies=blocked_companies,
                        unread_messages_count=unread_messages_count)

@bp.route('/search')
def search():
    # 後継者一覧ページにリダイレクト
    return redirect(url_for('main.successor_list'))

@bp.route('/successor/list')
def successor_list():
    page = request.args.get('page', 1, type=int)
    query = Successor.query.filter_by(is_public=True)
    
    # ブロックユーザーの除外
    if current_user.is_authenticated:
        blocked_ids = [block.blocked_id for block in current_user.blocking]
        blocking_ids = [block.blocker_id for block in current_user.blocked_by]
        query = query.join(User).filter(~User.id.in_(blocked_ids + blocking_ids))
    
    # 検索条件の適用
    search = request.args.get('search')
    industry = request.args.get('industry')
    location = request.args.get('location')
    investment_amount = request.args.get('investment_amount')
    
    if search:
        query = query.filter(
            db.or_(
                Successor.name.ilike(f'%{search}%'),
                Successor.industry.ilike(f'%{search}%'),
                Successor.description.ilike(f'%{search}%')
            )
        )
    if industry and industry != '':
        query = query.filter(Successor.desired_industry == industry)
    if location and location != '':
        query = query.filter(Successor.desired_location == location)
    if investment_amount and investment_amount != '':
        query = query.filter(Successor.investment_capacity == investment_amount)
    
    # ページネーション
    pagination = query.order_by(Successor.created_at.desc()).paginate(
        page=page, per_page=9, error_out=False)
    successors = pagination.items
    
    # お気に入りの後継者IDリストを取得
    favorite_successors = []
    if current_user.is_authenticated and current_user.user_type == 'company':
        favorite_successors = [s.id for s in current_user.favorite_successors]
    
    # 共通の選択肢を使用
    from app.utils.choices import INDUSTRY_CHOICES, LOCATION_CHOICES
    
    return render_template('main/successor_list.html',
                         title='後継者一覧',
                         successors=pagination,
                         pagination=pagination,
                         industries=INDUSTRY_CHOICES,
                         locations=LOCATION_CHOICES,
                         search=search,
                         favorite_successors=favorite_successors)

@bp.route('/successor/<int:id>')
def successor_detail(id):
    successor = Successor.query.get_or_404(id)
    return render_template('main/successor_detail.html',
                         title=successor.name,
                         successor=successor)

@bp.route('/successors/create', methods=['GET', 'POST'])
@login_required
def create_successor():
    if not current_user.is_company:
        flash('企業アカウントのみ後継者情報を登録できます。', 'error')
        return redirect(url_for('main.successor_list'))
    
    if request.method == 'POST':
        successor = Successor(
            name=request.form['name'],
            description=request.form['description'],
            requirements=request.form.get('requirements'),
            company_id=current_user.id
        )
        db.session.add(successor)
        db.session.commit()
        flash('後継者情報を登録しました。', 'success')
        return redirect(url_for('main.successor_detail', id=successor.id))
    
    return render_template('main/create_successor.html',
                         title='後継者情報の登録')

@bp.route('/successor/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_successor(id):
    successor = Successor.query.get_or_404(id)
    
    if successor.company_id != current_user.id:
        flash('この後継者情報を編集する権限がありません。', 'error')
        return redirect(url_for('main.successor_detail', id=id))
    
    if request.method == 'POST':
        successor.name = request.form['name']
        successor.description = request.form['description']
        successor.requirements = request.form.get('requirements')
        db.session.commit()
        flash('後継者情報を更新しました。', 'success')
        return redirect(url_for('main.successor_detail', id=id))
    
    return render_template('main/edit_successor.html',
                         title='後継者情報の編集',
                         successor=successor)

@bp.route('/successor/<int:id>/delete', methods=['POST'])
@login_required
def delete_successor(id):
    successor = Successor.query.get_or_404(id)
    
    if successor.company_id != current_user.id:
        flash('この後継者情報を削除する権限がありません。', 'error')
        return redirect(url_for('main.successor_detail', id=id))
    
    db.session.delete(successor)
    db.session.commit()
    flash('後継者情報を削除しました。', 'success')
    return redirect(url_for('main.successor_list'))

@bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    # 未読通知を既読にマーク
    current_user.notifications.filter_by(read=False).update({'read': True})
    db.session.commit()
    
    return render_template('main/notifications.html',
                         title='通知',
                         notifications=notifications)

@bp.route('/favorites')
@login_required
def favorites():
    if current_user.user_type == 'company':
        return redirect(url_for('main.company_favorites'))
    else:
        return redirect(url_for('main.successor_favorites'))

@bp.route('/company/favorites')
@login_required
def company_favorites():
    if current_user.user_type != 'company':
        flash('企業アカウントのみアクセスできます。', 'error')
        return redirect(url_for('main.successor_favorites'))
    favorite_successors = current_user.favorite_successors.all()
    return render_template('main/company_favorites.html', title='お気に入り企業', successors=favorite_successors)

@bp.route('/successor/favorites')
@login_required
def successor_favorites():
    if current_user.user_type != 'successor':
        flash('後継者アカウントのみアクセスできます。', 'error')
        return redirect(url_for('main.company_favorites'))
    
    page = request.args.get('page', 1, type=int)
    
    # お気に入りの企業を取得（既存のリレーションシップを使用）
    favorite_companies = current_user.favorite_companies.paginate(
        page=page, per_page=12, error_out=False
    )
    
    print("=== Successor Favorites Debug ===")
    print(f"Current user: {current_user}")
    print(f"Page: {page}")
    print(f"Total favorites: {favorite_companies.total if favorite_companies else 0}")
    
    return render_template('main/successor_favorites.html',
                         title='お気に入り企業一覧',
                         companies=favorite_companies)

@bp.route('/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    """ユーザーをブロックする"""
    if current_user.user_type == 'company':
        target_user = Successor.query.get_or_404(user_id)
        # チャットルームを探してブロック状態を更新
        chat_room = ChatRoom.query.filter_by(
            company_id=current_user.id,
            successor_id=target_user.id
        ).first()
        if chat_room:
            chat_room.company_blocked = True
            db.session.commit()
            flash('ユーザーをブロックしました', 'success')
    else:
        target_user = Company.query.get_or_404(user_id)
        # チャットルームを探してブロック状態を更新
        chat_room = ChatRoom.query.filter_by(
            company_id=target_user.id,
            successor_id=current_user.id
        ).first()
        if chat_room:
            chat_room.successor_blocked = True
            db.session.commit()
            flash('ユーザーをブロックしました', 'success')

    return redirect(url_for('main.profile', user_id=user_id))

@bp.route('/unblock_user/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    """ユーザーのブロックを解除する"""
    if current_user.user_type == 'company':
        target_user = Successor.query.get_or_404(user_id)
        chat_room = ChatRoom.query.filter_by(
            company_id=current_user.id,
            successor_id=target_user.id
        ).first()
        if chat_room:
            chat_room.company_blocked = False
            db.session.commit()
            flash('ブロックを解除しました', 'success')
    else:
        target_user = Company.query.get_or_404(user_id)
        chat_room = ChatRoom.query.filter_by(
            company_id=target_user.id,
            successor_id=current_user.id
        ).first()
        if chat_room:
            chat_room.successor_blocked = False
            db.session.commit()
            flash('ブロックを解除しました', 'success')

    return redirect(url_for('main.profile', user_id=user_id))

@bp.route('/blocked_users')
@login_required
def blocked_users():
    print("=== Blocked Users Debug ===")
    print(f"Current user: {current_user}")
    print(f"User type: {current_user.user_type}")
    
    page = request.args.get('page', 1, type=int)
    
    # 後継者ユーザーの場合は企業のみを、企業ユーザーの場合は後継者のみを表示
    if current_user.user_type == 'successor':
        query = Company.query.join(
            User, Company.user_id == User.id
        ).join(
            BlockedUser,
            (BlockedUser.blocked_id == User.id) & 
            (BlockedUser.blocker_id == current_user.id)
        )
        print("Querying blocked companies for successor")
    else:
        query = Successor.query.join(
            User, Successor.user_id == User.id
        ).join(
            BlockedUser,
            (BlockedUser.blocked_id == User.id) & 
            (BlockedUser.blocker_id == current_user.id)
        )
        print("Querying blocked successors for company")
    
    # ページネーション
    blocked_users = query.paginate(page=page, per_page=12, error_out=False)
    print(f"Found {blocked_users.total} blocked users")
    
    return render_template('main/blocked_users.html',
                         title='ブロックリスト',
                         blocked_users=blocked_users)

@bp.route('/messages')
@login_required
def message_list():
    """メッセージ一覧を表示"""
    if current_user.user_type == 'company':
        chat_rooms = ChatRoom.query.filter_by(user1_id=current_user.id).order_by(ChatRoom.last_message_at.desc()).all()
    else:
        chat_rooms = ChatRoom.query.filter_by(user2_id=current_user.id).order_by(ChatRoom.last_message_at.desc()).all()

    # 各チャットルームごとに未読件数を計算
    unread_counts = {}
    for room in chat_rooms:
        unread_count = Message.query.filter_by(
            chat_room_id=room.id,
            is_read=False
        ).filter(Message.sender_id != current_user.id).count()
        unread_counts[room.id] = unread_count

    return render_template('chat/chat_list.html', chat_rooms=chat_rooms, unread_counts=unread_counts)

@bp.route('/privacy-policy')
def privacy_policy():
    """プライバシーポリシーを表示"""
    return render_template('main/privacy_policy.html')

@bp.route('/terms-of-service')
def terms_of_service():
    """利用規約を表示"""
    return render_template('main/terms_of_service.html')

@bp.route('/faq')
def faq():
    """よくある質問を表示"""
    return render_template('main/faq.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """お問い合わせフォームを表示・処理"""
    form = ContactForm()
    if form.validate_on_submit():
        try:
            # お問い合わせデータを保存
            contact = Contact(
                name=form.name.data,
                email=form.email.data,
                subject=form.subject.data,
                message=form.message.data
            )
            db.session.add(contact)
            db.session.commit()

            try:
                # 確認メールを送信
                send_contact_confirmation(contact)
                # 管理者に通知
                send_contact_notification(contact)
                flash('お問い合わせを受け付けました。確認メールをお送りしましたので、ご確認ください。', 'success')
            except Exception as mail_error:
                current_app.logger.error(f'Mail sending error: {str(mail_error)}')
                flash('お問い合わせは受け付けましたが、確認メールの送信に失敗しました。', 'warning')
                # メール送信エラーの詳細をログに記録
                current_app.logger.error(f'Mail error details: {traceback.format_exc()}')

            return redirect(url_for('main.contact'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Contact form error: {str(e)}')
            current_app.logger.error(f'Error details: {traceback.format_exc()}')
            flash('申し訳ありません。エラーが発生しました。しばらく時間をおいて再度お試しください。', 'error')
    
    return render_template('main/contact.html', form=form)

@bp.route('/announcements')
def announcements():
    announcements = Announcement.query.filter_by(is_public=True).order_by(Announcement.created_at.desc()).all()
    return render_template('main/announcements.html', announcements=announcements)

@bp.route('/terms')
def terms():
    """利用規約を表示"""
    return render_template('main/terms.html')

@bp.route('/notes')
@login_required
def notes():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    return render_template('main/notes.html', notes=notes)

@bp.route('/notes/create', methods=['GET', 'POST'])
@login_required
def create_note():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(user_id=current_user.id, title=form.title.data, content=form.content.data)
        db.session.add(note)
        db.session.commit()
        flash('メモを作成しました', 'success')
        return redirect(url_for('main.notes'))
    return render_template('main/create_note.html', form=form)

@bp.route('/notes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id != current_user.id:
        flash('このメモを編集する権限がありません。', 'error')
        return redirect(url_for('main.notes'))
    form = NoteForm(obj=note)
    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data
        db.session.commit()
        flash('メモを更新しました', 'success')
        return redirect(url_for('main.notes'))
    return render_template('main/edit_note.html', form=form, note=note)

@bp.route('/notes/<int:id>/delete', methods=['POST'])
@login_required
def delete_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id != current_user.id:
        flash('このメモを削除する権限がありません。', 'error')
        return redirect(url_for('main.notes'))
    db.session.delete(note)
    db.session.commit()
    flash('メモを削除しました', 'success')
    return redirect(url_for('main.notes'))

@bp.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html')

@bp.route('/test-companies')
@login_required
def test_company_list():
    try:
        companies = Company.query.limit(5).all()
        return str([c.name for c in companies])
    except Exception as e:
        return f"Error: {str(e)}", 500

@bp.route('/companies')
def company_list():
    form = CompanySearchForm()
    page = request.args.get('page', 1, type=int)
    
    # 一般企業のみを表示（管理者と後継者を除外）
    query = Company.query.join(
        User, Company.user_id == User.id
    ).filter(
        Company.is_profile_completed == True,
        User.user_type == 'company',
        User.is_admin == False  # 管理者を明示的に除外
    )

    # ブロックユーザーの除外
    if current_user.is_authenticated:
        blocked_ids = [block.blocked_id for block in current_user.blocking]
        blocking_ids = [block.blocker_id for block in current_user.blocked_by]
        query = query.filter(~User.id.in_(blocked_ids + blocking_ids))

    # 検索条件の適用
    search = request.args.get('search')
    industry = request.args.get('industry')
    location = request.args.get('location')
    min_capital = request.args.get('min_capital', type=int)

    if search:
        query = query.filter(
            db.or_(
                Company.name.ilike(f'%{search}%'),
                Company.business_description.ilike(f'%{search}%'),
                Company.short_description.ilike(f'%{search}%')
            )
        )
    if industry and industry != '':
        query = query.filter(Company.industry == industry)
    if location and location != '':
        query = query.filter(Company.location == location)
    if min_capital:
        query = query.filter(Company.capital >= min_capital)

    # ページネーション
    pagination = query.order_by(Company.created_at.desc()).paginate(
        page=page, per_page=9, error_out=False)
    companies = pagination.items

    # お気に入りの企業IDリストを取得
    favorite_companies = []
    if current_user.is_authenticated and current_user.user_type == 'successor':
        favorite_companies = [c.id for c in current_user.favorite_companies]

    return render_template('main/company_list.html',
                         title='企業一覧',
                         form=form,
                         companies=pagination,
                         favorite_companies=favorite_companies)

@bp.route('/db_test')
# @login_required
def db_test():
    try:
        company = Company.query.first()
        if company:
            return f"OK: {company.name}"
        else:
            return "OK: companiesテーブルにデータがありません"
    except Exception as e:
        import traceback
        return f"DBエラー: {str(e)}<br><pre>{traceback.format_exc()}</pre>"

@bp.route('/settings/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        # 入力値をセッションに一時保存し、確認ページへ
        session['change_email'] = {
            'current_password': form.current_password.data,
            'new_email': form.new_email.data
        }
        return redirect(url_for('main.change_email_confirm'))
    # セッションの一時データは初期表示時にクリア
    session.pop('change_email', None)
    return render_template('main/change_email.html', title='メールアドレスの変更', form=form)

@bp.route('/settings/change-email/confirm', methods=['GET', 'POST'])
@login_required
def change_email_confirm():
    data = session.get('change_email')
    if not data:
        flash('最初からやり直してください。')
        return redirect(url_for('main.change_email'))
    if request.method == 'POST':
        # パスワード認証・メール送信処理
        form = ChangeEmailForm(data=data)
        if current_user.check_password(data['current_password']):
            token = create_verification_record(current_user.id, data['new_email'])
            verification_url = url_for('main.verify_email', token=token, _external=True)
            send_email(
                'メールアドレス変更の確認',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[data['new_email']],
                text_body=render_template('email/verify_email.txt', verification_url=verification_url),
                html_body=render_template('email/verify_email.html', verification_url=verification_url)
            )
            session.pop('change_email', None)
            return redirect(url_for('main.change_email_result', result='success'))
        else:
            flash('現在のパスワードが正しくありません。')
            return redirect(url_for('main.change_email'))
    return render_template('main/change_email_confirm.html', data=data)

@bp.route('/settings/change-email/result')
@login_required
def change_email_result():
    result = request.args.get('result')
    return render_template('main/change_email_result.html', result=result)

@bp.route('/verify-email/<token>')
@login_required
def verify_email(token):
    user_id, new_email = verify_token(token)
    if user_id and new_email and user_id == current_user.id:
        current_user.email = new_email
        db.session.commit()
        flash('メールアドレスが更新されました。')
    else:
        flash('無効なトークンです。')
    return redirect(url_for('main.settings'))

@bp.route('/settings/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            # パスワード変更通知を送信
            send_email(
                'パスワード変更のお知らせ',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[current_user.email],
                text_body=render_template('email/password_change_notification.txt',
                                        change_time=datetime.utcnow()),
                html_body=render_template('email/password_change_notification.html',
                                        change_time=datetime.utcnow())
            )
            flash('パスワードが更新されました。')
            return redirect(url_for('main.settings'))
        else:
            flash('現在のパスワードが正しくありません。')
    return render_template('main/change_password.html', title='パスワードの変更',
                         form=form)

@bp.route('/settings/deactivate', methods=['GET', 'POST'])
@login_required
def deactivate_account():
    form = DeactivateAccountForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            # 論理削除を実施
            current_user.is_active = False
            current_user.deactivated_at = datetime.utcnow()
            db.session.commit()
            logout_user()
            flash('アカウントが無効化されました。30日後に完全に削除されます。')
            return redirect(url_for('main.index'))
        else:
            flash('パスワードが正しくありません。')
    return render_template('main/deactivate.html', title='退会手続き',
                         form=form)

@bp.route('/admin/announcements')
@login_required
@admin_required
def admin_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements_list.html', announcements=announcements)

@bp.route('/admin/announcements/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_announcement_new():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        is_public = 'is_public' in request.form
        ann = Announcement(title=title, content=content, is_public=is_public)
        db.session.add(ann)
        db.session.commit()
        # 公開時に全ユーザーへ通知
        if is_public:
            users = User.query.filter_by(is_active=True).all()
            for user in users:
                notification = Notification(user_id=user.id, type='system', message=f'新しいお知らせ: {title}', link=f'/announcements/{ann.id}')
                notification.read = False
                db.session.add(notification)
            db.session.commit()
        flash('お知らせを追加しました。')
        return redirect(url_for('main.admin_announcements'))
    return render_template('admin/announcement_form.html', mode='new')

@bp.route('/admin/announcements/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_announcement_edit(id):
    ann = Announcement.query.get_or_404(id)
    if request.method == 'POST':
        ann.title = request.form['title']
        ann.content = request.form['content']
        was_public = ann.is_public
        ann.is_public = 'is_public' in request.form
        db.session.commit()
        # 非公開→公開に変更された場合のみ通知
        if not was_public and ann.is_public:
            users = User.query.filter_by(is_active=True).all()
            for user in users:
                notification = Notification(user_id=user.id, type='system', message=f'新しいお知らせ: {ann.title}', link=f'/announcements/{ann.id}')
                notification.read = False
                db.session.add(notification)
            db.session.commit()
        flash('お知らせを更新しました。')
        return redirect(url_for('main.admin_announcements'))
    return render_template('admin/announcement_form.html', mode='edit', announcement=ann)

@bp.route('/admin/announcements/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_announcement_delete(id):
    ann = Announcement.query.get_or_404(id)
    db.session.delete(ann)
    db.session.commit()
    flash('お知らせを削除しました。')
    return redirect(url_for('main.admin_announcements'))

@bp.route('/announcements/<int:id>')
def announcement_detail(id):
    ann = Announcement.query.get_or_404(id)
    return render_template('main/announcement_detail.html', announcement=ann) 