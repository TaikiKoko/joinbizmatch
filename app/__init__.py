from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config, ProductionConfig
from datetime import datetime
from markupsafe import Markup
import logging
import sys
from flask_socketio import SocketIO
from app.utils import template_filters

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flask_debug.log', mode='w')
    ]
)

# Socket.IOのロガー設定
socketio_logger = logging.getLogger('socketio')
socketio_logger.setLevel(logging.DEBUG)
engineio_logger = logging.getLogger('engineio')
engineio_logger.setLevel(logging.DEBUG)

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()

# Socket.IOの設定を最適化
socketio = SocketIO(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading',
    manage_session=True,
    ping_timeout=10000,
    ping_interval=5000,
    max_http_buffer_size=50 * 1024 * 1024,
    always_connect=True,
    reconnection=True,
    reconnection_attempts=10,
    reconnection_delay=1000,
    message_queue=None  # メモリキャッシュを使用
)

def format_datetime(value):
    if value is None:
        return ""
    return value.strftime('%Y年%m月%d日 %H:%M')

def format_currency(value):
    if value is None:
        return "0"
    return f"¥{value:,}"

def nl2br(value):
    if value:
        return Markup(value.replace('\n', '<br>'))
    return ''

def create_app(config_class=ProductionConfig):
    print('=== DEBUG: sys.path ===')
    print(sys.path)
    print('=======================')
    app = Flask(__name__)
    app.config.from_object(config_class)
    print('=== DEBUG: SQLALCHEMY_DATABASE_URI ===')
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    print('======================================')
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['JSON_AS_ASCII'] = False  # 日本語文字化け防止
    
    # WebSocketの設定
    app.config['SOCKETIO_PING_TIMEOUT'] = 10000
    app.config['SOCKETIO_PING_INTERVAL'] = 5000
    app.config['SOCKETIO_ASYNC_MODE'] = 'threading'
    app.config['SOCKETIO_MANAGE_SESSION'] = True
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # メール設定の初期化と確認
    mail.init_app(app)
    with app.app_context():
        try:
            mail.connect()
            app.logger.info("Mail server connection initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize mail server connection: {str(e)}")
    
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Socket.IOの初期化を最適化
    socketio.init_app(
        app,
        cookie=None,  # ← Noneに修正
        message_queue=None,  # ローカル開発用。本番環境では適切なメッセージキューを設定
        cors_allowed_origins="*"
    )
    
    # Register filters
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['nl2br'] = nl2br
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.profile import bp as profile_bp
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    from app.chat import bp as chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')
    
    # イベントハンドラをインポート（初期化後に行う）
    with app.app_context():
        from app import events
    
    template_filters.init_app(app)
    
    with app.app_context():
        # キャッシュの初期化
        from app.chat.cache import cache
        cache.ensure_initialized()
    
    @app.before_request
    def before_request():
        from app.chat.cache import cache
        cache.ensure_initialized()
    
    return app 