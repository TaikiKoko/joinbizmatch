import unittest
from app import create_app, db
from app.models.user import User
from app.models.chat_room import ChatRoom
from app.models.message import Message
from datetime import datetime

class TestChat(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # テストユーザーの作成
        self.company = User(
            username='test_company',
            email='company@example.com',
            user_type='company'
        )
        self.company.set_password('password')
        
        self.successor = User(
            username='test_successor',
            email='successor@example.com',
            user_type='successor'
        )
        self.successor.set_password('password')
        
        db.session.add_all([self.company, self.successor])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_chat_room(self):
        """チャットルーム作成のテスト"""
        chat_room = ChatRoom.get_or_create_room(
            company_id=self.company.id,
            successor_id=self.successor.id
        )
        self.assertIsNotNone(chat_room)
        self.assertEqual(chat_room.company_id, self.company.id)
        self.assertEqual(chat_room.successor_id, self.successor.id)

    def test_send_message(self):
        """メッセージ送信のテスト"""
        chat_room = ChatRoom.get_or_create_room(
            company_id=self.company.id,
            successor_id=self.successor.id
        )
        message = Message(
            chat_room_id=chat_room.id,
            sender_id=self.company.id,
            content='Test message'
        )
        db.session.add(message)
        db.session.commit()

        self.assertEqual(message.content, 'Test message')
        self.assertEqual(message.sender_id, self.company.id)
        self.assertFalse(message.is_read)

    def test_mark_as_read(self):
        """メッセージ既読のテスト"""
        chat_room = ChatRoom.get_or_create_room(
            company_id=self.company.id,
            successor_id=self.successor.id
        )
        message = Message(
            chat_room_id=chat_room.id,
            sender_id=self.company.id,
            content='Test message'
        )
        db.session.add(message)
        db.session.commit()

        message.is_read = True
        db.session.commit()
        self.assertTrue(message.is_read)

    def test_get_chat_rooms(self):
        """チャットルーム一覧取得のテスト"""
        chat_room = ChatRoom.get_or_create_room(
            company_id=self.company.id,
            successor_id=self.successor.id
        )
        with self.client as c:
            # 企業としてログイン
            c.post('/auth/company/login', data={
                'email': 'company@example.com',
                'password': 'password'
            }, follow_redirects=True)
            
            # チャットルーム一覧の取得
            response = c.get('/chat')
            self.assertEqual(response.status_code, 200)
            
            # 企業のチャットルームが正しく取得できることを確認
            self.assertIn(chat_room, self.company.chat_rooms.all())

    def test_chat_room_access(self):
        """チャットルームアクセス権限のテスト"""
        chat_room = ChatRoom.get_or_create_room(
            company_id=self.company.id,
            successor_id=self.successor.id
        )
        
        # 未認証ユーザーのアクセス
        response = self.client.get(f'/chat/{chat_room.id}')
        self.assertEqual(response.status_code, 302)  # ログインページにリダイレクト

        # 企業としてログイン
        with self.client as c:
            c.post('/auth/company/login', data={
                'email': 'company@example.com',
                'password': 'password'
            }, follow_redirects=True)
            
            # チャットルームへのアクセス
            response = c.get(f'/chat/{chat_room.id}')
            self.assertEqual(response.status_code, 200)
            
            # 存在しないチャットルームへのアクセス
            response = c.get('/chat/999')
            self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main() 