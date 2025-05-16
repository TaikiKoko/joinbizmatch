import os
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Debug prints
print("=== Environment Variables Debug ===")
print("Current working directory:", os.getcwd())
print("Basedir:", basedir)
print("Env file path:", os.path.join(basedir, '.env'))
print("MAIL_SERVER:", os.environ.get('MAIL_SERVER'))
print("MAIL_PORT:", os.environ.get('MAIL_PORT'))
print("MAIL_USERNAME:", os.environ.get('MAIL_USERNAME'))
print("================================")

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    DEBUG = True  # デバッグモードを有効化
    ENV = 'development'  # 開発環境を明示的に設定
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:4524Koko@localhost:5432/intoppy_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis設定
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    
    # メール設定
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.sendgrid.net')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'apikey')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'takeyuki.umeno@outlook.jp')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'takeyuki.umeno@outlook.jp')
    ADMINS = ['takeyuki.umeno@outlook.jp']
    POSTS_PER_PAGE = 25
    LANGUAGES = ['ja', 'en']
    
    # アップロード設定
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # ログ設定
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # セッション設定
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_TYPE = 'filesystem'
    
    @staticmethod
    def init_app(app):
        pass

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    
    # 本番環境では必ず環境変数から設定を読み込む
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # PostgreSQL設定
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:4524Koko@localhost:5432/intoppy_db'
    
    # セキュリティ設定
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # ログ設定
    LOG_TO_STDOUT = True
    
    @staticmethod
    def init_app(app):
        # 本番環境での初期化処理
        pass 