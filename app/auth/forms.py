from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保持')
    submit = SubmitField('ログイン')

class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'パスワード（確認）',
        validators=[DataRequired(), EqualTo('password', message='パスワードが一致しません。')]
    )
    submit = SubmitField('登録')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('このユーザー名は既に使用されています。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('このメールアドレスは既に登録されています。')

class CompanyRegistrationForm(FlaskForm):
    email = StringField('メールアドレス', validators=[
        DataRequired(message='メールアドレスを入力してください'),
        Email(message='有効なメールアドレスを入力してください')
    ])
    password = PasswordField('パスワード', validators=[
        DataRequired(message='パスワードを入力してください'),
        Length(min=8, message='パスワードは8文字以上である必要があります')
    ])
    password2 = PasswordField(
        'パスワード（確認）',
        validators=[
            DataRequired(message='確認用パスワードを入力してください'),
            EqualTo('password', message='パスワードが一致しません')
        ]
    )
    terms = BooleanField('利用規約に同意します', validators=[
        DataRequired(message='利用規約への同意が必要です')
    ])
    submit = SubmitField('企業として登録')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('このメールアドレスは既に登録されています。')

class SuccessorRegistrationForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[
        DataRequired(),
        Length(min=8, message='パスワードは8文字以上である必要があります')
    ])
    password2 = PasswordField(
        'パスワード（確認）',
        validators=[DataRequired(), EqualTo('password', message='パスワードが一致しません')]
    )
    terms = BooleanField('利用規約に同意します', validators=[DataRequired(message='利用規約への同意が必要です')])
    submit = SubmitField('後継者として登録')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('このメールアドレスは既に登録されています。')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    submit = SubmitField('パスワードリセット')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('新しいパスワード', validators=[DataRequired()])
    password2 = PasswordField(
        'パスワード（確認）',
        validators=[DataRequired(), EqualTo('password', message='パスワードが一致しません')]
    )
    submit = SubmitField('パスワードを更新') 