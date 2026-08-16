"""Property-based tests for password hashing.

Validates: Requirements 1.6, 2.1
"""

import string

from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import text

from app.models.user import User


# --------------------------------------------------------------------------
# Property 5: Password hashing round-trip
# **Validates: Requirements 1.6, 2.1**
# --------------------------------------------------------------------------


class TestPasswordHashingProperty:
    """Property 5: Password hashing round-trip.

    For any valid password string (8-128 characters), calling set_password
    followed by check_password with the same string SHALL return True, and
    the stored password_hash SHALL never equal the plaintext password.

    **Validates: Requirements 1.6, 2.1**
    """

    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(password=text(min_size=8, max_size=128, alphabet=string.printable))
    def test_check_password_returns_true_for_correct_password(self, app, password):
        """set_password followed by check_password with the same string returns True."""
        user = User(username="testuser", email="test@example.com")
        user.set_password(password)
        assert user.check_password(password) is True, (
            f"check_password should return True for the correct password"
        )

    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(password=text(min_size=8, max_size=128, alphabet=string.printable))
    def test_password_hash_never_equals_plaintext(self, app, password):
        """The stored password_hash SHALL never equal the plaintext password."""
        user = User(username="testuser", email="test@example.com")
        user.set_password(password)
        assert user.password_hash != password, (
            f"password_hash must not equal the plaintext password"
        )
