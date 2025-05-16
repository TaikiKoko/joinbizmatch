from flask import current_app
from flask_mail import Message
from app import mail
from threading import Thread
import logging
import traceback

logger = logging.getLogger(__name__)

def verify_smtp_connection():
    """SMTPサーバーへの接続を確認する"""
    try:
        with current_app.app_context():
            with mail.connect() as conn:
                logger.info(f"SMTP connection successful - Server: {current_app.config['MAIL_SERVER']}, Port: {current_app.config['MAIL_PORT']}, TLS: {current_app.config['MAIL_USE_TLS']}")
                return True
    except Exception as e:
        logger.error(f"SMTP connection failed: {str(e)}")
        logger.error(f"Mail settings: MAIL_SERVER={current_app.config.get('MAIL_SERVER')}, "
                    f"MAIL_PORT={current_app.config.get('MAIL_PORT')}, "
                    f"MAIL_USE_TLS={current_app.config.get('MAIL_USE_TLS')}, "
                    f"MAIL_USERNAME={current_app.config.get('MAIL_USERNAME')}")
        return False

def send_async_email(app, msg):
    """非同期でメールを送信する"""
    with app.app_context():
        try:
            logger.info(f"Attempting to send email to {msg.recipients}")
            logger.info(f"Mail server settings: MAIL_SERVER={app.config.get('MAIL_SERVER')}, "
                       f"MAIL_PORT={app.config.get('MAIL_PORT')}, "
                       f"MAIL_USE_TLS={app.config.get('MAIL_USE_TLS')}, "
                       f"MAIL_USERNAME={app.config.get('MAIL_USERNAME')}")
            
            mail.send(msg)
            logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            logger.error(f'Failed to send email: {str(e)}')
            logger.error(f'Mail server settings: MAIL_SERVER={app.config.get("MAIL_SERVER")}, '
                        f'MAIL_PORT={app.config.get("MAIL_PORT")}, '
                        f'MAIL_USE_TLS={app.config.get("MAIL_USE_TLS")}, '
                        f'MAIL_USERNAME={app.config.get("MAIL_USERNAME")}')
            logger.error(f'Error details: {traceback.format_exc()}')
            raise

def send_email(subject, sender, recipients, text_body, html_body=None):
    """メールを送信する"""
    try:
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        if html_body:
            msg.html = html_body
        
        logger.info(f"Preparing to send email: subject={subject}, sender={sender}, recipients={recipients}")
        
        # 非同期でメールを送信
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()
        
        logger.info(f"Email queued for sending to {recipients}")
    except Exception as e:
        logger.error(f"Failed to queue email: {str(e)}")
        logger.error(f'Error details: {traceback.format_exc()}')
        raise

def send_contact_confirmation(contact):
    """お問い合わせ確認メールを送信する"""
    try:
        send_email(
            subject='【INTOPPY TIME】お問い合わせを受け付けました',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[contact.email],
            text_body=f'''
{contact.name} 様

お問い合わせありがとうございます。
以下の内容で承りました：

件名：{contact.subject}
メッセージ：
{contact.message}

内容を確認次第、担当者よりご連絡させていただきます。
しばらくお待ちくださいますようお願いいたします。

※このメールは自動送信されています。返信はできませんのでご了承ください。

--
INTOPPY TIME
''')
        logger.info(f"Confirmation email queued for {contact.email}")
    except Exception as e:
        logger.error(f"Failed to queue confirmation email: {str(e)}")
        raise

def send_contact_notification(contact):
    """管理者へお問い合わせ通知メールを送信する"""
    try:
        admin_email = current_app.config['ADMIN_EMAIL']
        send_email(
            subject='【INTOPPY TIME】新規お問い合わせがありました',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[admin_email],
            text_body=f'''
新規のお問い合わせがありました。

送信者：{contact.name} <{contact.email}>
件名：{contact.subject}
メッセージ：
{contact.message}

管理画面から確認してください。
''')
        logger.info(f"Admin notification email queued for {admin_email}")
    except Exception as e:
        logger.error(f"Failed to queue admin notification: {str(e)}")
        raise 