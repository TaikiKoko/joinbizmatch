from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re

class ChangeEmailForm(FlaskForm):
    current_password = PasswordField('現在のパスワード', validators=[DataRequired(message='パスワードを入力してください')])
    new_email = StringField('新しいメールアドレス', validators=[
        DataRequired(message='メールアドレスを入力してください'),
        Email(message='有効なメールアドレスを入力してください')
    ])
    submit = SubmitField('変更する')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('現在のパスワード', validators=[DataRequired(message='現在のパスワードを入力してください')])
    new_password = PasswordField('新しいパスワード', validators=[
        DataRequired(message='新しいパスワードを入力してください'),
        Length(min=8, message='パスワードは8文字以上で入力してください')
    ])
    confirm_password = PasswordField('新しいパスワード（確認）', validators=[
        DataRequired(message='確認用パスワードを入力してください'),
        EqualTo('new_password', message='パスワードが一致しません')
    ])
    submit = SubmitField('変更する')

    def validate_new_password(self, field):
        # 英数字混在チェック
        if not (re.search(r'[A-Za-z]', field.data) and re.search(r'[0-9]', field.data)):
            raise ValidationError('パスワードは英字と数字を含める必要があります')

class DeactivateAccountForm(FlaskForm):
    current_password = PasswordField('現在のパスワード', validators=[DataRequired(message='パスワードを入力してください')])
    confirmation = StringField('確認のため「退会します」と入力してください', validators=[
        DataRequired(message='確認文を入力してください'),
        EqualTo('退会します', message='「退会します」と正確に入力してください')
    ])
    submit = SubmitField('退会する') 