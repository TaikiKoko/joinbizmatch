from app import create_app, db
from config import ProductionConfig
from datetime import datetime
import os
from sqlalchemy import text

def export_database():
    # アプリケーションコンテキストの作成
    app = create_app(ProductionConfig)
    
    with app.app_context():
        # バックアップファイル名の生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'intoppy_db_backup_{timestamp}.sql'
        
        try:
            # データベースの内容を取得
            with open(backup_file, 'w', encoding='utf-8') as f:
                # テーブル一覧の取得
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                
                for table in tables:
                    # テーブルの構造を取得
                    columns = inspector.get_columns(table)
                    create_table = f"CREATE TABLE IF NOT EXISTS {table} (\n"
                    create_table += ",\n".join([f"    {col['name']} {col['type']}" for col in columns])
                    create_table += "\n);\n\n"
                    f.write(create_table)
                    
                    # テーブルのデータを取得
                    query = text(f"SELECT * FROM {table}")
                    result = db.session.execute(query)
                    for row in result:
                        values = [f"'{str(val)}'" if val is not None else 'NULL' for val in row]
                        insert = f"INSERT INTO {table} VALUES ({', '.join(values)});\n"
                        f.write(insert)
                    f.write("\n")
            
            print(f'バックアップが正常に完了しました: {backup_file}')
        except Exception as e:
            print(f'バックアップ中にエラーが発生しました: {e}')

if __name__ == '__main__':
    export_database() 