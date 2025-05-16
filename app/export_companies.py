import sqlite3

# SQLite DBファイルに接続
conn = sqlite3.connect('instance/app.db')
cur = conn.cursor()

# companiesテーブルからIDと会社名を取得
cur.execute("SELECT id, name FROM companies;")
rows = cur.fetchall()

print("ID\tCompanyName")
for row in rows:
    print(f"{row[0]}\t{row[1]}")

conn.close()
