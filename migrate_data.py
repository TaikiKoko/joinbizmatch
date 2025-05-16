import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# SQLiteデータベースの接続
sqlite_conn = sqlite3.connect('app.db')
sqlite_cursor = sqlite_conn.cursor()

# PostgreSQLデータベースの接続
pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
pg_cursor = pg_conn.cursor()

def get_table_names():
    """SQLiteデータベースのテーブル一覧を取得"""
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [table[0] for table in sqlite_cursor.fetchall()]

def get_table_schema(table_name):
    """テーブルのスキーマ情報を取得"""
    sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
    return sqlite_cursor.fetchall()

def migrate_table(table_name):
    """テーブルのデータを移行"""
    print(f"Migrating table: {table_name}")
    
    # テーブルのデータを取得
    sqlite_cursor.execute(f"SELECT * FROM {table_name};")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"No data in table {table_name}")
        return
    
    # カラム名を取得
    columns = [col[1] for col in get_table_schema(table_name)]
    
    # PostgreSQLにデータを挿入
    insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s;"
    execute_values(pg_cursor, insert_query, rows)
    
    print(f"Migrated {len(rows)} rows from {table_name}")

def main():
    try:
        # テーブル一覧を取得
        tables = get_table_names()
        
        # 各テーブルのデータを移行
        for table in tables:
            if table != 'sqlite_sequence':  # SQLiteのシステムテーブルはスキップ
                migrate_table(table)
        
        # 変更をコミット
        pg_conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        pg_conn.rollback()
    finally:
        # 接続を閉じる
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

if __name__ == "__main__":
    main() 