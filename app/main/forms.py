from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional
from app.utils.choices import INDUSTRY_CHOICES, LOCATION_CHOICES

class ContactForm(FlaskForm):
    name = StringField('お名前', validators=[DataRequired(), Length(max=100)])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    subject = SelectField('お問い合わせ種類', choices=[
        ('general', '一般的な質問'),
        ('technical', '技術的な問題'),
        ('billing', '料金・支払い'),
        ('other', 'その他')
    ])
    message = TextAreaField('お問い合わせ内容', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('送信')

class NoteForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('保存')

class CompanySearchForm(FlaskForm):
    industry = SelectField('業種', choices=[('', '選択してください')] + INDUSTRY_CHOICES, validators=[Optional()])
    location = SelectField('所在地', choices=[('', '選択してください')] + LOCATION_CHOICES, validators=[Optional()])
    min_capital = IntegerField('売却希望額（万円以上）', validators=[Optional()])
    search = StringField('フリーワード', validators=[Optional(), Length(max=100)])
    submit = SubmitField('検索') 