"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()

            User.query.delete()
            Message.query.delete()
            Likes.query.delete()
            Follows.query.delete()

            self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

            db.session.add(self.testuser)
            db.session.commit()
            
            self.testuser_id = self.testuser.id
            
            self.u1 = User.signup(username="abc", email="test1@test.com", password="password", image_url=None)
            db.session.add(self.u1)
            db.session.commit()
            self.u1_id = self.u1.id

            self.u2 = User.signup(username="efg", email="test2@test.com", password="password", image_url=None)
            db.session.add(self.u2)
            db.session.commit()
            self.u2_id = self.u2.id

            self.u3 = User.signup(username="hij", email="test3@test.com", password="password", image_url=None)
            db.session.add(self.u3)
            db.session.commit()
            self.u3_id = self.u3.id

            self.u4 = User.signup(username="testing", email="test4@test.com", password="password", image_url=None)
            db.session.add(self.u4)
            db.session.commit()
            self.u4_id = self.u4.id

            db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction"""
        with app.app_context():
            resp = super().tearDown()
            db.session.rollback()
            return resp
        
    def test_users_index(self):
        """Test that the users index page displays correct users."""
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))
            self.assertIn("@hij", str(resp.data))
            self.assertIn("@testing", str(resp.data))

    def test_users_search(self):
        """Test that the users search function returns correct users."""
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@testing", str(resp.data))            

            self.assertNotIn("@abc", str(resp.data))
            self.assertNotIn("@efg", str(resp.data))
            self.assertNotIn("@hij", str(resp.data))

    def test_user_show(self):
        """Test that user profile page is displayed correctly."""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))

    def test_user_show_with_likes_and_follows(self):
        """Test that user profile page correctly displays likes and follows information."""
        with app.app_context():
            with self.client as c:
                # Make testuser follow u1 and u2, and be followed by u3 and u4
                f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
                f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
                f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u3_id)
                f4 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u4_id)

                # Create messages
                m1 = Message(text="abc", user_id=self.testuser_id)
                m2 = Message(text="efg", user_id=self.testuser_id)
                m3 = Message(text="hij", user_id=self.testuser_id)

                db.session.add_all([f1, f2, f3, f4, m1, m2, m3])
                db.session.commit()

                # Make testuser like m1 and m2
                l1 = Likes(user_id=self.testuser_id, message_id=m1.id)
                l2 = Likes(user_id=self.testuser_id, message_id=m2.id)

                db.session.add_all([l1, l2])
                db.session.commit()

                resp = c.get(f"/users/{self.testuser_id}")
                self.assertEqual(resp.status_code, 200)

                soup = BeautifulSoup(resp.data, 'html.parser')
                stats = soup.find_all('li', class_='stat')

                messages_count = int(stats[0].h4.a.text)
                following_count = int(stats[1].h4.a.text)
                followers_count = int(stats[2].h4.a.text)
                likes_count = int(stats[3].h4.a.text)

                self.assertEqual(messages_count, 3)  # 3 messages
                self.assertEqual(following_count, 2)  # 2 following
                self.assertEqual(followers_count, 2)  # 2 followers
                self.assertEqual(likes_count, 2)  # 2 likes

    def test_toggle_like(self):
        """Test that like is added and removed correctly."""
        with app.app_context():
            with self.client as c:
                m = Message(text="Hello, world!", user_id=self.u1_id)
                db.session.add(m)
                db.session.commit()
                
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser_id

                resp = c.post(f"/users/add_like/{m.id}")

                self.assertEqual(resp.status_code, 302)  

                likes = Likes.query.filter(Likes.message_id==m.id).all()
                self.assertEqual(len(likes), 1)
                self.assertEqual(likes[0].user_id, self.testuser_id)
               
                resp = c.post(f"/users/add_like/{m.id}")  # unlikes the message

                self.assertEqual(resp.status_code, 302)  

                # Check that the like has been removed
                likes = Likes.query.filter(Likes.message_id==m.id).all()
                self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        """Test that unauthenticated user cannot add a like."""
        with app.app_context():
            with self.client as c:
                m = Message(text="Hello, world!", user_id=self.u1_id)
                db.session.add(m)
                db.session.commit()

                resp = c.post(f"/users/add_like/{m.id}") # tries to like message without being logged in

                self.assertEqual(resp.status_code, 302)  # the route redirects to login page

                likes = Likes.query.filter(Likes.message_id==m.id).all()
                self.assertEqual(len(likes), 0)


def test_user_cannot_like_own_message(self):
    """Test that a user cannot like their own message."""
    with app.app_context():
        with self.client as c:
            m = Message(text="Hello, world!", user_id=self.u1_id)
            db.session.add(m)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/add_like/{m.id}")
            self.assertEqual(resp.status_code, 302) 

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

    
