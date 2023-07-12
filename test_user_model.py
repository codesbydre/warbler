"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError


from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data




class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            db.create_all()

            self.client = app.test_client()

            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            self.password1 = "hashed_password"
            self.password2 = "hashed_password2"

            u1 = User.signup("testuser", self.password1, "test@test.com", "test image", "test location")
            u2 = User.signup("testuser2", self.password2, "test2@test.com", "test image2", "test location")
            db.session.add_all([u1, u2])
            db.session.commit()

            self.u1 = db.session.get(User, u1.id)
            self.u2 = db.session.get(User, u2.id)

    def tearDown(self):
        """Clean up any fouled transaction."""

        with app.app_context():
            db.session.rollback()
            db.drop_all()
            db.session.commit()

    def test_user_model(self):
        """Does basic model work?"""
        with app.app_context():
            u = User(
                email="testing@test.com",
                username="testinguser",
                password="HASHED_PASSWORD"
        )

            db.session.add(u)
            db.session.commit()

             # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)

    def test_user_repr(self):
        """Does the repr method work as expected?"""
        with app.app_context():
            self.assertEqual(repr(self.u1), f"<User #{self.u1.id}: {self.u1.username}, {self.u1.email}>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""
        with app.app_context():
            self.u1 = db.session.merge(self.u1)
            self.u2 = db.session.merge(self.u2)

            self.u1.following.append(self.u2)
            db.session.commit()

            self.assertTrue(self.u1.is_following(self.u2))
            self.assertFalse(self.u2.is_following(self.u1))

    def test_is_not_following(self):
        """Does is_following successfully detect when user1 is not following user2?"""
        with app.app_context():
            self.u1 = db.session.merge(self.u1)
            self.u2 = db.session.merge(self.u2)

            self.assertFalse(self.u1.is_following(self.u2))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""
        with app.app_context():
            self.u1 = db.session.merge(self.u1)
            self.u2 = db.session.merge(self.u2)

            self.u1.following.append(self.u2)
            db.session.commit()

            self.assertTrue(self.u2.is_followed_by(self.u1))

    def test_is_not_followed_by(self):
        """Does is_followed_by successfully detect when user1 is not followed by user2?"""
        with app.app_context():
            self.u1 = db.session.merge(self.u1)
            self.u2 = db.session.merge(self.u2)

            self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_user_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""
        with app.app_context():
            user = User.signup("testuser3", "hashed_password3", "test3@test.com", "test image3", "test location")
            db.session.commit()

            u_test = db.session.get(User, user.id)
            self.assertIsNotNone(u_test)

    def test_user_signup_fail(self):
        """Does User.signup fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""
        with app.app_context():
            with self.assertRaises(IntegrityError):
                User.signup("testuser", "test@test.com", "hashed_password", "test image", "test location")
                db.session.commit()

    def test_user_authenticate(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""
        with app.app_context():
            self.u1 = db.session.merge(self.u1)
            user = User.authenticate("testuser", self.password1)
            self.assertIsNotNone(user)
            if user:
                self.assertEqual(user.id, self.u1.id)

    def test_user_authenticate_fail_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""
        with app.app_context():
            user = User.authenticate("invalidusername", "hashed_password")
            self.assertFalse(user)

    def test_user_authenticate_fail_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""
        with app.app_context():
            user = User.authenticate("testuser", "invalidpassword")
            self.assertFalse(user)
