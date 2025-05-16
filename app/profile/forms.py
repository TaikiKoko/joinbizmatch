from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, SelectField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, URL, Optional, NumberRange
from datetime import datetime

class ProfileForm(FlaskForm):
    profile_image = FileField('プロフィール画像',
                            validators=[FileAllowed(['jpg', 'png', 'jpeg'], '画像ファイルのみアップロード可能です。')])
    bio = TextAreaField('自己紹介',
                       validators=[DataRequired(message='自己紹介を入力してください。'),
                                 Length(min=10, max=500, message='自己紹介は10文字以上500文字以下で入力してください。')])
    location = StringField('場所',
                         validators=[Optional(), Length(max=100)])
    website = StringField('ウェブサイト',
                        validators=[Optional(), URL(message='有効なURLを入力してください。')])
    submit = SubmitField('保存')

class CompanyProfileForm(FlaskForm):
    company_name = StringField('会社名', validators=[DataRequired(), Length(max=100)])
    industry = SelectField('業種', choices=[
        ('none', '特になし'),
        ('manufacturing', '製造業'),
        ('retail', '小売業'),
        ('service', 'サービス業'),
        ('it', 'IT・通信'),
        ('construction', '建設業'),
        ('food', '飲食業'),
        ('real_estate', '不動産業'),
        ('medical', '医療・福祉'),
        ('education', '教育'),
        ('agriculture', '農林水産業'),
        ('other', 'その他')
    ])
    location = SelectField('所在地', choices=[
        ('未設定', '未設定'),
        ('北海道', '北海道'),
        ('青森県', '青森県'),
        ('岩手県', '岩手県'),
        ('宮城県', '宮城県'),
        ('秋田県', '秋田県'),
        ('山形県', '山形県'),
        ('福島県', '福島県'),
        ('茨城県', '茨城県'),
        ('栃木県', '栃木県'),
        ('群馬県', '群馬県'),
        ('埼玉県', '埼玉県'),
        ('千葉県', '千葉県'),
        ('東京都', '東京都'),
        ('神奈川県', '神奈川県'),
        ('新潟県', '新潟県'),
        ('富山県', '富山県'),
        ('石川県', '石川県'),
        ('福井県', '福井県'),
        ('山梨県', '山梨県'),
        ('長野県', '長野県'),
        ('岐阜県', '岐阜県'),
        ('静岡県', '静岡県'),
        ('愛知県', '愛知県'),
        ('三重県', '三重県'),
        ('滋賀県', '滋賀県'),
        ('京都府', '京都府'),
        ('大阪府', '大阪府'),
        ('兵庫県', '兵庫県'),
        ('奈良県', '奈良県'),
        ('和歌山県', '和歌山県'),
        ('鳥取県', '鳥取県'),
        ('島根県', '島根県'),
        ('岡山県', '岡山県'),
        ('広島県', '広島県'),
        ('山口県', '山口県'),
        ('徳島県', '徳島県'),
        ('香川県', '香川県'),
        ('愛媛県', '愛媛県'),
        ('高知県', '高知県'),
        ('福岡県', '福岡県'),
        ('佐賀県', '佐賀県'),
        ('長崎県', '長崎県'),
        ('熊本県', '熊本県'),
        ('大分県', '大分県'),
        ('宮崎県', '宮崎県'),
        ('鹿児島県', '鹿児島県'),
        ('沖縄県', '沖縄県')
    ])
    employee_count = IntegerField('従業員数', validators=[DataRequired(), NumberRange(min=0)])
    established_year = IntegerField('設立年', validators=[DataRequired(), NumberRange(min=1800, max=2100)])
    annual_revenue = IntegerField('年間売上（万円）', validators=[DataRequired(), NumberRange(min=0)])
    operating_profit = IntegerField('営業利益（万円）', validators=[DataRequired()])
    capital = IntegerField('資本金（万円）', validators=[DataRequired(), NumberRange(min=0)])
    business_description = TextAreaField('事業内容', validators=[DataRequired()])
    short_description = StringField('企業紹介文（カード表示用）', validators=[Optional(), Length(max=200)])
    succession_reason = TextAreaField('売却理由', validators=[DataRequired()])
    desired_conditions = TextAreaField('希望条件', validators=[DataRequired()])
    company_images = FileField('会社画像（任意）')
    website = StringField('ウェブサイト',
                        validators=[Optional(), URL(message='有効なURLを入力してください。')])
    homepage = StringField('ホームページ', validators=[Optional(), URL(message='有効なURLを入力してください。')])
    instagram = StringField('インスタグラム', validators=[Optional(), URL(message='有効なURLを入力してください。')])
    twitter = StringField('ツイッター', validators=[Optional(), URL(message='有効なURLを入力してください。')])
    submit = SubmitField('保存')

class SuccessorProfileForm(FlaskForm):
    # Basic Information
    name = StringField('名前', validators=[DataRequired(), Length(max=100)])
    age = IntegerField('年齢', validators=[Optional(), NumberRange(min=18, max=100)])
    gender = SelectField('性別', choices=[
        ('未設定', '未設定'),
        ('男性', '男性'),
        ('女性', '女性'),
        ('その他', 'その他')
    ])
    location = SelectField('現在の所在地', choices=[
        ('未設定', '未設定'),
        ('北海道', '北海道'),
        ('青森県', '青森県'),
        ('岩手県', '岩手県'),
        ('宮城県', '宮城県'),
        ('秋田県', '秋田県'),
        ('山形県', '山形県'),
        ('福島県', '福島県'),
        ('茨城県', '茨城県'),
        ('栃木県', '栃木県'),
        ('群馬県', '群馬県'),
        ('埼玉県', '埼玉県'),
        ('千葉県', '千葉県'),
        ('東京都', '東京都'),
        ('神奈川県', '神奈川県'),
        ('新潟県', '新潟県'),
        ('富山県', '富山県'),
        ('石川県', '石川県'),
        ('福井県', '福井県'),
        ('山梨県', '山梨県'),
        ('長野県', '長野県'),
        ('岐阜県', '岐阜県'),
        ('静岡県', '静岡県'),
        ('愛知県', '愛知県'),
        ('三重県', '三重県'),
        ('滋賀県', '滋賀県'),
        ('京都府', '京都府'),
        ('大阪府', '大阪府'),
        ('兵庫県', '兵庫県'),
        ('奈良県', '奈良県'),
        ('和歌山県', '和歌山県'),
        ('鳥取県', '鳥取県'),
        ('島根県', '島根県'),
        ('岡山県', '岡山県'),
        ('広島県', '広島県'),
        ('山口県', '山口県'),
        ('徳島県', '徳島県'),
        ('香川県', '香川県'),
        ('愛媛県', '愛媛県'),
        ('高知県', '高知県'),
        ('福岡県', '福岡県'),
        ('佐賀県', '佐賀県'),
        ('長崎県', '長崎県'),
        ('熊本県', '熊本県'),
        ('大分県', '大分県'),
        ('宮崎県', '宮崎県'),
        ('鹿児島県', '鹿児島県'),
        ('沖縄県', '沖縄県')
    ])
    description = TextAreaField('自己紹介', validators=[Optional(), Length(max=1000)])
    
    # Desired Conditions
    desired_industry = SelectField('希望業界', choices=[
        ('none', '特になし'),
        ('manufacturing', '製造業'),
        ('retail', '小売業'),
        ('service', 'サービス業'),
        ('it', 'IT・通信'),
        ('construction', '建設業'),
        ('food', '飲食業'),
        ('real_estate', '不動産業'),
        ('medical', '医療・福祉'),
        ('education', '教育'),
        ('agriculture', '農林水産業'),
        ('other', 'その他')
    ])
    desired_location = SelectField('希望地域', choices=[
        ('未設定', '未設定'),
        ('北海道', '北海道'),
        ('青森県', '青森県'),
        ('岩手県', '岩手県'),
        ('宮城県', '宮城県'),
        ('秋田県', '秋田県'),
        ('山形県', '山形県'),
        ('福島県', '福島県'),
        ('茨城県', '茨城県'),
        ('栃木県', '栃木県'),
        ('群馬県', '群馬県'),
        ('埼玉県', '埼玉県'),
        ('千葉県', '千葉県'),
        ('東京都', '東京都'),
        ('神奈川県', '神奈川県'),
        ('新潟県', '新潟県'),
        ('富山県', '富山県'),
        ('石川県', '石川県'),
        ('福井県', '福井県'),
        ('山梨県', '山梨県'),
        ('長野県', '長野県'),
        ('岐阜県', '岐阜県'),
        ('静岡県', '静岡県'),
        ('愛知県', '愛知県'),
        ('三重県', '三重県'),
        ('滋賀県', '滋賀県'),
        ('京都府', '京都府'),
        ('大阪府', '大阪府'),
        ('兵庫県', '兵庫県'),
        ('奈良県', '奈良県'),
        ('和歌山県', '和歌山県'),
        ('鳥取県', '鳥取県'),
        ('島根県', '島根県'),
        ('岡山県', '岡山県'),
        ('広島県', '広島県'),
        ('山口県', '山口県'),
        ('徳島県', '徳島県'),
        ('香川県', '香川県'),
        ('愛媛県', '愛媛県'),
        ('高知県', '高知県'),
        ('福岡県', '福岡県'),
        ('佐賀県', '佐賀県'),
        ('長崎県', '長崎県'),
        ('熊本県', '熊本県'),
        ('大分県', '大分県'),
        ('宮崎県', '宮崎県'),
        ('鹿児島県', '鹿児島県'),
        ('沖縄県', '沖縄県')
    ])
    investment_capacity = SelectField('投資可能額', choices=[
        ('未設定', '未設定'),
        ('～1000万円', '～1000万円'),
        ('1000万円～3000万円', '1000万円～3000万円'),
        ('3000万円～5000万円', '3000万円～5000万円'),
        ('5000万円～1億円', '5000万円～1億円'),
        ('1億円以上', '1億円以上')
    ])
    
    # Experience
    management_experience = TextAreaField('経営経験', validators=[Optional(), Length(max=1000)])
    industry_experience = TextAreaField('業界経験', validators=[Optional(), Length(max=1000)])
    
    # Privacy Settings
    is_public = BooleanField('プロフィールを公開する')
    
    # プロフィール画像
    images = FileField('プロフィール画像（任意）', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '画像ファイルのみアップロード可能です。')])
    
    submit = SubmitField('保存') 