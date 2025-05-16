import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.company import Company

def add_test_company():
    app = create_app()
    with app.app_context():
        # 既存のテストデータを削除（オプション）
        Company.query.filter_by(name="テスト株式会社").delete()
        
        # 新しいテストデータを追加
        company = Company(
            name="テスト株式会社",
            description="これはテスト用の企業です。",
            industry="IT",
            location="東京都",
            is_active=True
        )
        db.session.add(company)
        db.session.commit()
        print("テストデータを追加しました。")

if __name__ == '__main__':
    add_test_company() 