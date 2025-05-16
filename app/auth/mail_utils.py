from threading import Thread
from flask_mail import Message
from flask import render_template
from app import mail

def get_app():
    from flask import current_app
    return current_app

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    app = get_app()
    Thread(target=send_async_email,
           args=(app._get_current_object(), msg)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    app = get_app()
    send_email(
        'パスワードリセット',
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt',
                                user=user, token=token),
        html_body=render_template('email/reset_password.html',
                                user=user, token=token)
    )

def send_verification_email(user):
    token = user.get_verification_token()
    app = get_app()
    send_email(
        'メールアドレスの認証',
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/verify_email.txt',
                                user=user, token=token),
        html_body=render_template('email/verify_email.html',
                                user=user, token=token)
    ) 