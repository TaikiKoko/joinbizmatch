from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class SellerRegistrationForm(FlaskForm):
    company_name = StringField('企業名', validators=[
        DataRequired(message='企業名は必須です'),
        Length(max=100, message='企業名は100文字以内で入力してください')
    ])
    representative_name = StringField('代表者名', validators=[
        DataRequired(message='代表者名は必須です'),
        Length(max=100, message='代表者名は100文字以内で入力してください')
    ])
    establishment_year = IntegerField('設立年', validators=[
        DataRequired(message='設立年は必須です'),
        NumberRange(min=1800, max=2024, message='有効な設立年を入力してください')
    ])
    capital = IntegerField('資本金（万円）', validators=[
        Optional(),
        NumberRange(min=0, message='資本金は0以上で入力してください')
    ])
    employees = IntegerField('従業員数', validators=[
        Optional(),
        NumberRange(min=0, message='従業員数は0以上で入力してください')
    ])
    annual_sales = IntegerField('年間売上（万円）', validators=[
        Optional(),
        NumberRange(min=0, message='年間売上は0以上で入力してください')
    ])
    business_description = TextAreaField('事業内容', validators=[
        Optional(),
        Length(max=1000, message='事業内容は1000文字以内で入力してください')
    ])
    reason_for_sale = TextAreaField('売却理由', validators=[
        Optional(),
        Length(max=1000, message='売却理由は1000文字以内で入力してください')
    ])
    desired_successor = TextAreaField('希望する後継者像', validators=[
        Optional(),
        Length(max=1000, message='希望する後継者像は1000文字以内で入力してください')
    ])
    asking_price = IntegerField('希望価格（万円）', validators=[
        Optional(),
        NumberRange(min=0, message='希望価格は0以上で入力してください')
    ])

class SellerEditForm(SellerRegistrationForm):
    is_active = BooleanField('アクティブ') 