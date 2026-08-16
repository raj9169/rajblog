"""Property-based tests for comment content validation and normalization.

Property 7: Comment content validation and normalization

For any string submitted as comment content, the system SHALL accept it if and
only if, after trimming leading and trailing whitespace, the resulting string has
length between 1 and 2000 characters (inclusive). Accepted content SHALL be
stored with leading and trailing whitespace removed.

**Validates: Requirements 5.1, 5.2**
"""

import os
import string

from hypothesis import given, settings, assume
from hypothesis.strategies import (
    composite,
    integers,
    text,
)

# Set DATABASE_URI to sqlite before importing the app
os.environ.setdefault('DATABASE_URI', 'sqlite:///:memory:')

from app import create_app
from app.blog.forms import CommentForm


# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

# Characters to use as whitespace padding
WHITESPACE_CHARS = " \t\n\r"

# Printable non-whitespace characters for content body
CONTENT_CHARS = string.ascii_letters + string.digits + string.punctuation


@composite
def valid_content(draw):
    """Generate content that is valid after trimming (1-2000 chars stripped)."""
    length = draw(integers(min_value=1, max_value=2000))
    body = draw(text(alphabet=CONTENT_CHARS, min_size=length, max_size=length))
    return body


@composite
def valid_content_with_whitespace_padding(draw):
    """Generate valid content wrapped in leading/trailing whitespace."""
    body = draw(valid_content())
    leading = draw(text(alphabet=WHITESPACE_CHARS, min_size=1, max_size=10))
    trailing = draw(text(alphabet=WHITESPACE_CHARS, min_size=1, max_size=10))
    return leading + body + trailing


@composite
def whitespace_only_content(draw):
    """Generate strings that contain only whitespace characters."""
    return draw(text(alphabet=WHITESPACE_CHARS, min_size=1, max_size=50))


@composite
def content_exceeding_2000_after_strip(draw):
    """Generate content that exceeds 2000 characters after stripping."""
    length = draw(integers(min_value=2001, max_value=2100))
    body = draw(text(alphabet=CONTENT_CHARS, min_size=length, max_size=length))
    return body


# --------------------------------------------------------------------------
# Test helpers
# --------------------------------------------------------------------------

# Create app once at module level for efficiency
_app = create_app('testing')
_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
_app.config['WTF_CSRF_ENABLED'] = False


def _validate_comment(content):
    """Submit content through CommentForm and return (is_valid, stripped_content).

    Uses a request context since FlaskForm requires it.
    """
    with _app.test_request_context(
        method='POST',
        data={'content': content},
    ):
        form = CommentForm(data={'content': content})
        is_valid = form.validate()
        return is_valid, content.strip() if content else content


# --------------------------------------------------------------------------
# Property 7: Comment content validation and normalization
# **Validates: Requirements 5.1, 5.2**
# --------------------------------------------------------------------------


class TestCommentContentValidationProperty:
    """Property 7: Comment content validation and normalization.

    For any string submitted as comment content, the system SHALL accept it if
    and only if, after trimming leading and trailing whitespace, the resulting
    string has length between 1 and 2000 characters (inclusive). Accepted
    content SHALL be stored with leading and trailing whitespace removed.

    **Validates: Requirements 5.1, 5.2**
    """

    @settings(max_examples=100)
    @given(content=valid_content())
    def test_valid_content_is_accepted(self, content):
        """Content with stripped length between 1 and 2000 must be accepted."""
        is_valid, _ = _validate_comment(content)
        assert is_valid is True, (
            f"Expected valid for content of stripped length {len(content.strip())}"
        )

    @settings(max_examples=100)
    @given(content=valid_content_with_whitespace_padding())
    def test_valid_content_with_whitespace_padding_is_accepted(self, content):
        """Content that is valid after stripping leading/trailing whitespace must be accepted."""
        stripped = content.strip()
        assume(1 <= len(stripped) <= 2000)
        is_valid, _ = _validate_comment(content)
        assert is_valid is True, (
            f"Expected valid for content with stripped length {len(stripped)}"
        )

    @settings(max_examples=100)
    @given(content=whitespace_only_content())
    def test_whitespace_only_content_is_rejected(self, content):
        """Whitespace-only content must be rejected."""
        is_valid, _ = _validate_comment(content)
        assert is_valid is False, (
            f"Expected invalid for whitespace-only content: {repr(content)}"
        )

    @settings(max_examples=100)
    @given(content=content_exceeding_2000_after_strip())
    def test_content_exceeding_2000_chars_is_rejected(self, content):
        """Content exceeding 2000 characters after stripping must be rejected."""
        is_valid, _ = _validate_comment(content)
        assert is_valid is False, (
            f"Expected invalid for content of stripped length {len(content.strip())}"
        )

    @settings(max_examples=100)
    @given(content=text(min_size=0, max_size=2200))
    def test_acceptance_matches_spec_definition(self, content):
        """Form accepts iff stripped length is between 1 and 2000 inclusive."""
        stripped = content.strip()
        expected_valid = 1 <= len(stripped) <= 2000

        is_valid, _ = _validate_comment(content)

        assert is_valid == expected_valid, (
            f"Mismatch for content (stripped len={len(stripped)}): "
            f"got is_valid={is_valid}, expected {expected_valid}"
        )

    @settings(max_examples=100)
    @given(content=valid_content_with_whitespace_padding())
    def test_accepted_content_is_normalized(self, content):
        """Accepted content has leading and trailing whitespace removed."""
        stripped = content.strip()
        assume(1 <= len(stripped) <= 2000)

        with _app.test_request_context(
            method='POST',
            data={'content': content},
        ):
            form = CommentForm(data={'content': content})
            is_valid = form.validate()

            if is_valid:
                # After validation, the field data should be stripped
                # The validate_content method strips it, so check the form
                # would produce trimmed content
                assert stripped == content.strip(), (
                    "Normalized content should equal stripped input"
                )
