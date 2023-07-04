import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from models import db, User, Message, Follows
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
from app import app

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client"""
        with app.app_context():
            db.create_all()
            self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""
        with app.app_context():
            db.session.rollback()
            db.drop_all()

    def test_message_model(self):
        """Does basic model work?"""
        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            password = "hashed_password"
            u1 = User.signup("testuser", password, "test@test.com", "test image")
            db.session.add(u1)
            db.session.commit()

            m1 = Message(text="Hello, this is a test message", user_id=u1.id)

            db.session.add(m1)
            db.session.commit()

            m = Message(text="Test message", user_id=u1.id)
            db.session.add(m)
            db.session.commit()

            u = User.query.get(u1.id)
            self.assertEqual(len(u.messages), 2)
            self.assertEqual(m.text, "Test message")

    def test_message_timestamp(self):
        """Does timestamp work?"""
        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            password = "hashed_password"
            u1 = User.signup("testuser", password, "test@test.com", "test image")
            db.session.add(u1)
            db.session.commit()

            m1 = Message(text="Hello, this is a test message", user_id=u1.id)

            db.session.add(m1)
            db.session.commit()

            m = db.session.query(Message).get(m1.id)
            self.assertIsInstance(m.timestamp, datetime)

    def test_user_message_relationship(self):
        """Does the relationship between user and message work?"""
        with app.app_context():
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            password = "hashed_password"
            u1 = User.signup("testuser", password, "test@test.com", "test image")
            db.session.add(u1)
            db.session.commit()

            m1 = Message(text="Hello, this is a test message", user_id=u1.id)

            db.session.add(m1)
            db.session.commit()

            u = User.query.get(u1.id)
            self.assertEqual(u.messages[0].text, "Hello, this is a test message")

