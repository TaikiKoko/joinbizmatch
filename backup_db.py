import os
import subprocess
from datetime import datetime

def backup_database():
    # バックアップファイル名の生成
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'intoppy_db_backup_{timestamp}.sql'
    
    # データベース接続情報
    db_name = 'intoppy_db'
    db_user = 'postgres'
    db_password = '4524Koko'
    db_host = 'localhost'
    
    # バックアップコマンドの構築
    backup_command = f'pg_dump -U {db_user} -h {db_host} {db_name} > {backup_file}'
    
    # 環境変数の設定
    os.environ['PGPASSWORD'] = db_password
    
    try:
        # バックアップの実行
        subprocess.run(backup_command, shell=True, check=True)
        print(f'バックアップが正常に完了しました: {backup_file}')
    except subprocess.CalledProcessError as e:
        print(f'バックアップ中にエラーが発生しました: {e}')
    finally:
        # 環境変数のクリーンアップ
        os.environ.pop('PGPASSWORD', None)

if __name__ == '__main__':
    backup_database() 