"""Unit tests for the User model."""

import pytest

from app.extensions import db as _db
from app.models.user import User


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app):
        """User can be created with required fields."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            _db.session.add(user)
            _db.session.commit()

            assert user.id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.created_at is not None
            assert user.updated_at is not None

    def test_set_password_hashes(self, app):
        """set_password stores a hash, not plain text."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('mysecret')
        assert user.password_hash != 'mysecret'
        assert user.password_hash is not None

    def test_check_password_correct(self, app):
        """check_password returns True for the correct password."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('mysecret')
        assert user.check_password('mysecret') is True

    def test_check_password_incorrect(self, app):
        """check_password returns False for an incorrect password."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('mysecret')
        assert user.check_password('wrongpassword') is False

    def test_username_unique_constraint(self, app):
        """Duplicate usernames raise an integrity error."""
        with app.app_context():
            user1 = User(username='duplicate', email='a@example.com')
            user1.set_password('pass1')
            _db.session.add(user1)
            _db.session.commit()

            user2 = User(username='duplicate', email='b@example.com')
            user2.set_password('pass2')
            _db.session.add(user2)
            with pytest.raises(Exception):
                _db.session.commit()

    def test_email_unique_constraint(self, app):
        """Duplicate emails raise an integrity error."""
        with app.app_context():
            user1 = User(username='user1', email='same@example.com')
            user1.set_password('pass1')
            _db.session.add(user1)
            _db.session.commit()

            user2 = User(username='user2', email='same@example.com')
            user2.set_password('pass2')
            _db.session.add(user2)
            with pytest.raises(Exception):
                _db.session.commit()

    def test_user_mixin_properties(self, app):
        """User inherits Flask-Login's UserMixin properties."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('pass')
        assert user.is_authenticated is True
        assert user.is_active is True
        assert user.is_anonymous is False

    def test_user_repr(self, app):
        """User repr shows username."""
        user = User(username='testuser', email='test@example.com')
        assert repr(user) == '<User testuser>'

    def test_user_loader(self, app):
        """user_loader callback retrieves user by ID."""
        with app.app_context():
            user = User(username='loadtest', email='load@example.com')
            user.set_password('pass')
            _db.session.add(user)
            _db.session.commit()

            loaded = User.query.get(user.id)
            assert loaded is not None
            assert loaded.username == 'loadtest'
