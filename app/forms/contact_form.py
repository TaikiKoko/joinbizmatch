from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    name = StringField('お名前', validators=[DataRequired(), Length(max=64)])
    email = StringField('メールアドレス', validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField('件名', validators=[DataRequired(), Length(max=120)])
    message = TextAreaField('メッセージ', validators=[DataRequired()])
    submit = SubmitField('送信') 