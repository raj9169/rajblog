"""Tests for authentication forms."""

import pytest
from werkzeug.datastructures import MultiDict

from app.auth.forms import LoginForm, RegistrationForm


class TestRegistrationForm:
    """Tests for RegistrationForm validation."""

    def test_valid_registration(self, app):
        """Valid data passes all validators."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'testuser',
                    'email': 'test@example.com',
                    'password': 'securepass1',
                    'confirm_password': 'securepass1',
                }
            )
            assert form.validate()

    def test_username_too_short(self, app):
        """Username under 3 chars fails validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'ab',
                    'email': 'test@example.com',
                    'password': 'securepass1',
                    'confirm_password': 'securepass1',
                }
            )
            assert not form.validate()
            assert 'username' in form.errors

    def test_username_too_long(self, app):
        """Username over 30 chars fails validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'a' * 31,
                    'email': 'test@example.com',
                    'password': 'securepass1',
                    'confirm_password': 'securepass1',
                }
            )
            assert not form.validate()
            assert 'username' in form.errors

    def test_username_invalid_chars(self, app):
        """Username with special characters fails validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'user@name!',
                    'email': 'test@example.com',
                    'password': 'securepass1',
                    'confirm_password': 'securepass1',
                }
            )
            assert not form.validate()
            assert 'username' in form.errors

    def test_username_valid_chars(self, app):
        """Username with letters, digits, underscores, hyphens passes."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'user_name-123',
                    'email': 'test@example.com',
                    'password': 'securepass1',
                    'confirm_password': 'securepass1',
                }
            )
            assert form.validate()

    def test_email_required(self, app):
        """Empty email fails validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'testuser',
                    'email': '',
                    'password': 'securepass1',
                    'confirm_password': 'securepass1',
                }
            )
            assert not form.validate()
            assert 'email' in form.errors

    def test_email_invalid_format(self, app):
        """Invalid email format fails validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'testuser',
                    'email': 'notanemail',
                    'password': 'securepass1',
                    'confirm_password': 'securepass1',
                }
            )
            assert not form.validate()
            assert 'email' in form.errors

    def test_password_too_short(self, app):
        """Password under 8 chars fails validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'testuser',
                    'email': 'test@example.com',
                    'password': 'short',
                    'confirm_password': 'short',
                }
            )
            assert not form.validate()
            assert 'password' in form.errors

    def test_password_too_long(self, app):
        """Password over 128 chars fails validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'testuser',
                    'email': 'test@example.com',
                    'password': 'x' * 129,
                    'confirm_password': 'x' * 129,
                }
            )
            assert not form.validate()
            assert 'password' in form.errors

    def test_password_mismatch(self, app):
        """Mismatched passwords fail validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': 'testuser',
                    'email': 'test@example.com',
                    'password': 'securepass1',
                    'confirm_password': 'differentpass',
                }
            )
            assert not form.validate()
            assert 'confirm_password' in form.errors

    def test_username_required(self, app):
        """Empty username fails validation."""
        with app.test_request_context():
            form = RegistrationForm(
                data={
                    'username': '',
                    'email': 'test@example.com',
                    'password': 'securepass1',
                    'confirm_password': 'securepass1',
                }
            )
            assert not form.validate()
            assert 'username' in form.errors


class TestLoginForm:
    """Tests for LoginForm validation."""

    def test_valid_login(self, app):
        """Valid email and password passes validation."""
        with app.test_request_context():
            form = LoginForm(
                data={
                    'email': 'test@example.com',
                    'password': 'securepass1',
                }
            )
            assert form.validate()

    def test_email_required(self, app):
        """Empty email fails validation."""
        with app.test_request_context():
            form = LoginForm(
                data={
                    'email': '',
                    'password': 'securepass1',
                }
            )
            assert not form.validate()
            assert 'email' in form.errors

    def test_password_required(self, app):
        """Empty password fails validation."""
        with app.test_request_context():
            form = LoginForm(
                data={
                    'email': 'test@example.com',
                    'password': '',
                }
            )
            assert not form.validate()
            assert 'password' in form.errors

    def test_both_fields_required(self, app):
        """Both empty fields fail validation."""
        with app.test_request_context():
            form = LoginForm(
                data={
                    'email': '',
                    'password': '',
                }
            )
            assert not form.validate()
            assert 'email' in form.errors
            assert 'password' in form.errors
