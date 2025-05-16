from app.utils.choices import INDUSTRY_CHOICES

def init_app(app):
    """テンプレートフィルターを初期化"""
    app.jinja_env.filters['industry_name'] = industry_name_filter

def industry_name_filter(industry_code):
    """業種コードを日本語名に変換"""
    if not industry_code:
        return '未設定'
    
    industry_dict = dict(INDUSTRY_CHOICES)
    return industry_dict.get(industry_code, industry_code) 