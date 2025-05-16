import os
import shutil
from app import create_app, db

def reset_database():
    # 既存のデータベースファイルを削除
    if os.path.exists('app.db'):
        os.remove('app.db')
    
    # 既存のマイグレーションディレクトリを削除
    if os.path.exists('migrations'):
        shutil.rmtree('migrations')
    
    # アプリケーションコンテキストを作成
    app = create_app()
    
    with app.app_context():
        # データベースを初期化
        db.create_all()
        
        print("データベースが正常にリセットされました。")

if __name__ == '__main__':
    reset_database() 