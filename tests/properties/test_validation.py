"""Property-based tests for validation utilities.

Validates: Requirements 1.7, 1.8
"""

import re
import string

from hypothesis import given, settings
from hypothesis.strategies import (
    composite,
    integers,
    just,
    one_of,
    sampled_from,
    text,
)

from app.utils import validate_email, validate_username

# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

VALID_USERNAME_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

# Characters that are NOT valid in a username
INVALID_USERNAME_CHARS = " !@#$%^&*()+=[]{}|;:'\",.<>?/~`"


@composite
def valid_usernames(draw):
    """Generate strings that are valid usernames (3-30 chars, valid chars only)."""
    return draw(text(alphabet=VALID_USERNAME_CHARS, min_size=3, max_size=30))


@composite
def too_short_usernames(draw):
    """Generate strings that are too short (1-2 chars, valid chars)."""
    return draw(text(alphabet=VALID_USERNAME_CHARS, min_size=1, max_size=2))


@composite
def too_long_usernames(draw):
    """Generate strings that are too long (31+ chars, valid chars)."""
    return draw(text(alphabet=VALID_USERNAME_CHARS, min_size=31, max_size=60))


@composite
def bad_char_usernames(draw):
    """Generate strings of valid length (3-30) but with at least one invalid char."""
    # Generate a valid-length base string
    length = draw(integers(min_value=3, max_value=30))
    # Build a string with at least one invalid character
    valid_part = draw(text(alphabet=VALID_USERNAME_CHARS, min_size=max(0, length - 1), max_size=max(0, length - 1)))
    invalid_char = draw(sampled_from(INVALID_USERNAME_CHARS))
    # Insert the invalid char at a random position
    pos = draw(integers(min_value=0, max_value=len(valid_part)))
    result = valid_part[:pos] + invalid_char + valid_part[pos:]
    return result


@composite
def valid_emails(draw):
    """Generate strings that satisfy the email validation rules."""
    # Local part: at least 1 char, no @
    local = draw(text(
        alphabet=string.ascii_letters + string.digits + "._+-",
        min_size=1,
        max_size=60,
    ))
    # Domain label: at least 1 char
    domain_label = draw(text(
        alphabet=string.ascii_lowercase + string.digits,
        min_size=1,
        max_size=20,
    ))
    # TLD: at least 1 char
    tld = draw(text(
        alphabet=string.ascii_lowercase,
        min_size=2,
        max_size=6,
    ))
    email = f"{local}@{domain_label}.{tld}"
    # Ensure total length <= 254
    if len(email) > 254:
        # Trim local part to fit
        excess = len(email) - 254
        local = local[: len(local) - excess]
        if not local:
            local = "a"
        email = f"{local}@{domain_label}.{tld}"
    return email


@composite
def emails_no_at(draw):
    """Generate strings without any @ character."""
    return draw(text(
        alphabet=string.ascii_letters + string.digits + ".",
        min_size=1,
        max_size=50,
    ))


@composite
def emails_multiple_at(draw):
    """Generate strings with more than one @ character."""
    local = draw(text(alphabet=string.ascii_letters, min_size=1, max_size=10))
    middle = draw(text(alphabet=string.ascii_letters, min_size=1, max_size=10))
    domain = draw(text(alphabet=string.ascii_lowercase, min_size=1, max_size=10))
    tld = draw(text(alphabet=string.ascii_lowercase, min_size=2, max_size=4))
    return f"{local}@{middle}@{domain}.{tld}"


@composite
def emails_no_dot_in_domain(draw):
    """Generate emails with no dot in the domain part."""
    local = draw(text(alphabet=string.ascii_letters, min_size=1, max_size=20))
    domain = draw(text(alphabet=string.ascii_lowercase + string.digits, min_size=1, max_size=20))
    return f"{local}@{domain}"


@composite
def emails_too_long(draw):
    """Generate emails exceeding 254 characters."""
    # Make a local part long enough to exceed 254 total
    local = draw(text(alphabet=string.ascii_letters, min_size=245, max_size=260))
    email = f"{local}@example.com"
    # Ensure it's over 254
    if len(email) <= 254:
        local = local + "a" * (255 - len(email))
        email = f"{local}@example.com"
    return email


# --------------------------------------------------------------------------
# Property 3: Username validation correctness
# **Validates: Requirements 1.7**
# --------------------------------------------------------------------------


class TestUsernameValidationProperty:
    """Property 3: Username validation correctness.

    For any string, validate_username SHALL return valid if and only if the
    string is between 3 and 30 characters in length (inclusive) and contains
    only letters, digits, underscores, or hyphens.

    **Validates: Requirements 1.7**
    """

    @settings(max_examples=100)
    @given(username=valid_usernames())
    def test_valid_usernames_are_accepted(self, username):
        """Valid usernames (3-30 chars, valid chars) must be accepted."""
        is_valid, error = validate_username(username)
        assert is_valid is True, f"Expected valid for '{username}', got error: {error}"
        assert error is None

    @settings(max_examples=100)
    @given(username=too_short_usernames())
    def test_too_short_usernames_are_rejected(self, username):
        """Usernames shorter than 3 characters must be rejected."""
        is_valid, error = validate_username(username)
        assert is_valid is False, f"Expected invalid for too-short '{username}'"
        assert error is not None

    @settings(max_examples=100)
    @given(username=too_long_usernames())
    def test_too_long_usernames_are_rejected(self, username):
        """Usernames longer than 30 characters must be rejected."""
        is_valid, error = validate_username(username)
        assert is_valid is False, f"Expected invalid for too-long '{username}'"
        assert error is not None

    @settings(max_examples=100)
    @given(username=bad_char_usernames())
    def test_invalid_char_usernames_are_rejected(self, username):
        """Usernames with invalid characters must be rejected."""
        is_valid, error = validate_username(username)
        assert is_valid is False, f"Expected invalid for '{username}' (contains bad chars)"
        assert error is not None

    @settings(max_examples=100)
    @given(username=text(min_size=0, max_size=80))
    def test_validation_matches_spec_definition(self, username):
        """validate_username returns valid iff 3<=len<=30 and all chars in [a-zA-Z0-9_-]."""
        is_valid, _ = validate_username(username)

        # Compute expected result from the spec definition
        valid_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        expected_valid = (
            3 <= len(username) <= 30
            and valid_pattern.match(username) is not None
        )

        assert is_valid == expected_valid, (
            f"Mismatch for '{username}': got {is_valid}, expected {expected_valid}"
        )


# --------------------------------------------------------------------------
# Property 4: Email validation correctness
# **Validates: Requirements 1.8**
# --------------------------------------------------------------------------


class TestEmailValidationProperty:
    """Property 4: Email validation correctness.

    For any string, validate_email SHALL return valid if and only if the string
    contains exactly one @ character, the portion after @ contains at least one
    dot, and the total length does not exceed 254 characters.

    **Validates: Requirements 1.8**
    """

    @settings(max_examples=100)
    @given(email=valid_emails())
    def test_valid_emails_are_accepted(self, email):
        """Emails with one @, dot in domain, and <=254 chars must be accepted."""
        result = validate_email(email)
        assert result is True, f"Expected valid for '{email}'"

    @settings(max_examples=100)
    @given(email=emails_no_at())
    def test_emails_without_at_are_rejected(self, email):
        """Strings without @ must be rejected."""
        result = validate_email(email)
        assert result is False, f"Expected invalid for '{email}' (no @ sign)"

    @settings(max_examples=100)
    @given(email=emails_multiple_at())
    def test_emails_with_multiple_at_are_rejected(self, email):
        """Strings with more than one @ must be rejected."""
        result = validate_email(email)
        assert result is False, f"Expected invalid for '{email}' (multiple @ signs)"

    @settings(max_examples=100)
    @given(email=emails_no_dot_in_domain())
    def test_emails_without_dot_in_domain_are_rejected(self, email):
        """Emails where domain has no dot must be rejected."""
        result = validate_email(email)
        assert result is False, f"Expected invalid for '{email}' (no dot in domain)"

    @settings(max_examples=100)
    @given(email=emails_too_long())
    def test_emails_exceeding_254_chars_are_rejected(self, email):
        """Emails longer than 254 characters must be rejected."""
        result = validate_email(email)
        assert result is False, f"Expected invalid for email of length {len(email)}"
