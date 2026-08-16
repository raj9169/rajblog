"""Tests for authentication routes (register, login, logout)."""

import time

import pytest

from app.extensions import db
from app.models.user import User


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    user = User(username='existing', email='existing@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


class TestRegisterRoute:
    """Tests for the /register route."""

    def test_register_get(self, client):
        """GET /register returns the registration form."""
        response = client.get('/register')
        assert response.status_code == 200

    def test_register_success(self, client):
        """Successful registration redirects to login with flash."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass1',
            'confirm_password': 'securepass1',
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

        # Verify user created in database
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.check_password('securepass1')

    def test_register_duplicate_username(self, client, sample_user):
        """Registration with existing username shows error."""
        response = client.post('/register', data={
            'username': 'existing',
            'email': 'different@example.com',
            'password': 'securepass1',
            'confirm_password': 'securepass1',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Username is already taken' in response.data

    def test_register_duplicate_email(self, client, sample_user):
        """Registration with existing email shows error."""
        response = client.post('/register', data={
            'username': 'differentuser',
            'email': 'existing@example.com',
            'password': 'securepass1',
            'confirm_password': 'securepass1',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Email is already registered' in response.data

    def test_register_invalid_form(self, client):
        """Registration with invalid form data re-renders form."""
        response = client.post('/register', data={
            'username': '',
            'email': 'bad',
            'password': 'short',
            'confirm_password': 'nomatch',
        })
        assert response.status_code == 200

    def test_register_empty_fields(self, client):
        """Registration with all empty fields shows validation errors."""
        response = client.post('/register', data={
            'username': '',
            'email': '',
            'password': '',
            'confirm_password': '',
        })
        assert response.status_code == 200
        assert b'Username is required' in response.data or b'This field is required' in response.data

    def test_register_password_too_short(self, client):
        """Registration with password shorter than 8 chars shows error."""
        response = client.post('/register', data={
            'username': 'validuser',
            'email': 'valid@example.com',
            'password': 'short',
            'confirm_password': 'short',
        })
        assert response.status_code == 200
        assert b'Password must be between 8 and 128 characters' in response.data

    def test_register_password_too_long(self, client):
        """Registration with password longer than 128 chars shows error."""
        long_password = 'a' * 129
        response = client.post('/register', data={
            'username': 'validuser',
            'email': 'valid@example.com',
            'password': long_password,
            'confirm_password': long_password,
        })
        assert response.status_code == 200
        assert b'Password must be between 8 and 128 characters' in response.data

    def test_register_invalid_username_format(self, client):
        """Registration with special characters in username shows error."""
        response = client.post('/register', data={
            'username': 'bad user!@#',
            'email': 'valid@example.com',
            'password': 'securepass1',
            'confirm_password': 'securepass1',
        })
        assert response.status_code == 200
        assert b'Username may only contain letters, digits, underscores, or hyphens' in response.data

    def test_register_invalid_email_format(self, client):
        """Registration with invalid email format shows error."""
        response = client.post('/register', data={
            'username': 'validuser',
            'email': 'not-an-email',
            'password': 'securepass1',
            'confirm_password': 'securepass1',
        })
        assert response.status_code == 200
        assert b'Please enter a valid email address' in response.data or b'Invalid email' in response.data

    def test_register_redirects_authenticated(self, client, sample_user):
        """Authenticated user is redirected away from register page."""
        # Login first
        client.post('/login', data={
            'email': 'existing@example.com',
            'password': 'password123',
        })
        response = client.get('/register', follow_redirects=False)
        assert response.status_code == 302


class TestLoginRoute:
    """Tests for the /login route."""

    def test_login_get(self, client):
        """GET /login returns the login form."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_success(self, client, sample_user):
        """Successful login redirects to dashboard."""
        response = client.post('/login', data={
            'email': 'existing@example.com',
            'password': 'password123',
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']

    def test_login_empty_fields(self, client):
        """Login with empty fields re-renders form with errors."""
        response = client.post('/login', data={
            'email': '',
            'password': '',
        })
        assert response.status_code == 200
        assert b'Email is required' in response.data or b'This field is required' in response.data

    def test_login_invalid_email(self, client, sample_user):
        """Login with wrong email shows error."""
        response = client.post('/login', data={
            'email': 'wrong@example.com',
            'password': 'password123',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_invalid_password(self, client, sample_user):
        """Login with wrong password shows error."""
        response = client.post('/login', data={
            'email': 'existing@example.com',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_redirects_authenticated(self, client, sample_user):
        """Authenticated user is redirected away from login page."""
        client.post('/login', data={
            'email': 'existing@example.com',
            'password': 'password123',
        })
        response = client.get('/login', follow_redirects=False)
        assert response.status_code == 302

    def test_login_next_parameter(self, client, sample_user):
        """Login redirects to next parameter URL after success."""
        response = client.post('/login?next=/post/new', data={
            'email': 'existing@example.com',
            'password': 'password123',
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/post/new' in response.headers['Location']

    def test_login_rejects_external_next(self, client, sample_user):
        """Login ignores external URLs in next parameter."""
        response = client.post('/login?next=http://evil.com', data={
            'email': 'existing@example.com',
            'password': 'password123',
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']

    def test_login_rejects_protocol_relative_next(self, client, sample_user):
        """Login ignores protocol-relative URLs in next parameter."""
        response = client.post('/login?next=//evil.com', data={
            'email': 'existing@example.com',
            'password': 'password123',
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']


class TestLogoutRoute:
    """Tests for the /logout route."""

    def test_logout_success(self, client, sample_user):
        """Logout clears session and redirects to home."""
        # Login first
        client.post('/login', data={
            'email': 'existing@example.com',
            'password': 'password123',
        })
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert '/' in response.headers['Location']

    def test_logout_requires_login(self, client):
        """Logout redirects unauthenticated users to login."""
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


class TestSessionInactivity:
    """Tests for session inactivity timeout."""

    def test_session_timeout_logs_out_user(self, app, client, sample_user):
        """User is logged out after inactivity timeout."""
        # Login
        client.post('/login', data={
            'email': 'existing@example.com',
            'password': 'password123',
        })

        # Simulate inactivity by setting last_activity in the past
        with client.session_transaction() as sess:
            sess['last_activity'] = time.time() - 1860  # 31 minutes ago

        # Next request should detect inactivity and log out
        response = client.get('/register', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_active_session_updates_last_activity(self, client, sample_user):
        """Active sessions have their last_activity updated."""
        # Login
        client.post('/login', data={
            'email': 'existing@example.com',
            'password': 'password123',
        })

        # Make a request within timeout
        client.get('/register')

        with client.session_transaction() as sess:
            assert 'last_activity' in sess
