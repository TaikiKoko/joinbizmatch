import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT')
}

def get_sqlite_data():
    """Get data from SQLite database"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    data = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT * FROM {table_name}")
        data[table_name] = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        data[f"{table_name}_columns"] = columns
    
    conn.close()
    return data

def migrate_to_postgres(data):
    """Migrate data to PostgreSQL"""
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    for table_name in [t for t in data.keys() if not t.endswith('_columns')]:
        columns = data[f"{table_name}_columns"]
        rows = data[table_name]
        
        if not rows:
            continue
            
        # Create table if not exists
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join([f"{col} TEXT" for col in columns])}
        );
        """
        cursor.execute(create_table_sql)
        
        # Insert data
        insert_sql = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES %s
        ON CONFLICT DO NOTHING;
        """
        execute_values(cursor, insert_sql, rows)
    
    conn.commit()
    conn.close()

def main():
    print("Starting database migration...")
    
    # Get data from SQLite
    print("Reading data from SQLite...")
    data = get_sqlite_data()
    
    # Migrate to PostgreSQL
    print("Migrating data to PostgreSQL...")
    migrate_to_postgres(data)
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    main() 