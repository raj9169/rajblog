"""Unit tests for utility functions."""

import pytest

from app.utils import generate_slug, sanitize_input, validate_email, validate_username


class TestGenerateSlug:
    """Tests for the generate_slug function."""

    def test_basic_title(self):
        assert generate_slug("Hello World") == "hello-world"

    def test_converts_to_lowercase(self):
        assert generate_slug("My GREAT Post") == "my-great-post"

    def test_replaces_multiple_spaces_with_single_hyphen(self):
        assert generate_slug("hello   world") == "hello-world"

    def test_removes_special_characters(self):
        assert generate_slug("Hello, World! How's it going?") == "hello-world-hows-it-going"

    def test_trims_leading_trailing_hyphens(self):
        assert generate_slug("--hello--") == "hello"

    def test_handles_tabs_and_newlines(self):
        assert generate_slug("hello\tworld\nnow") == "hello-world-now"

    def test_numeric_title(self):
        assert generate_slug("123 456") == "123-456"

    def test_mixed_alphanumeric(self):
        assert generate_slug("Post #1: My First Blog") == "post-1-my-first-blog"

    def test_all_special_characters_returns_empty(self):
        assert generate_slug("!@#$%^&*()") == ""

    def test_empty_title_returns_empty(self):
        assert generate_slug("") == ""

    def test_deduplication_appends_suffix(self):
        existing = ["hello-world"]
        assert generate_slug("Hello World", existing) == "hello-world-1"

    def test_deduplication_increments_suffix(self):
        existing = ["hello-world", "hello-world-1", "hello-world-2"]
        assert generate_slug("Hello World", existing) == "hello-world-3"

    def test_no_conflict_no_suffix(self):
        existing = ["other-post"]
        assert generate_slug("Hello World", existing) == "hello-world"

    def test_none_existing_slugs(self):
        assert generate_slug("Hello World", None) == "hello-world"

    def test_consecutive_hyphens_collapsed(self):
        assert generate_slug("hello---world") == "hello-world"


class TestValidateEmail:
    """Tests for the validate_email function."""

    def test_valid_email(self):
        assert validate_email("user@example.com") is True

    def test_valid_email_with_subdomain(self):
        assert validate_email("user@mail.example.com") is True

    def test_missing_at_sign(self):
        assert validate_email("userexample.com") is False

    def test_multiple_at_signs(self):
        assert validate_email("user@@example.com") is False

    def test_no_dot_in_domain(self):
        assert validate_email("user@localhost") is False

    def test_empty_email(self):
        assert validate_email("") is False

    def test_exceeds_254_characters(self):
        long_email = "a" * 246 + "@test.com"  # 246 + 9 = 255 characters
        assert validate_email(long_email) is False

    def test_empty_local_part(self):
        assert validate_email("@example.com") is False

    def test_empty_domain(self):
        assert validate_email("user@") is False

    def test_domain_starts_with_dot(self):
        assert validate_email("user@.example.com") is False

    def test_domain_ends_with_dot(self):
        assert validate_email("user@example.") is False

    def test_exactly_254_characters(self):
        # Create an email that's exactly 254 characters
        local = "a" * 243
        email = f"{local}@example.com"  # 243 + 1 + 7 + 1 + 3 = 255... adjust
        local = "a" * 240
        email = f"{local}@example.com"  # 240 + 1 + 11 = 252
        assert validate_email(email) is True


class TestValidateUsername:
    """Tests for the validate_username function."""

    def test_valid_username(self):
        is_valid, error = validate_username("john_doe")
        assert is_valid is True
        assert error is None

    def test_valid_with_hyphens(self):
        is_valid, error = validate_username("john-doe")
        assert is_valid is True
        assert error is None

    def test_valid_with_digits(self):
        is_valid, error = validate_username("user123")
        assert is_valid is True
        assert error is None

    def test_minimum_length(self):
        is_valid, error = validate_username("abc")
        assert is_valid is True
        assert error is None

    def test_maximum_length(self):
        is_valid, error = validate_username("a" * 30)
        assert is_valid is True
        assert error is None

    def test_too_short(self):
        is_valid, error = validate_username("ab")
        assert is_valid is False
        assert "at least 3" in error

    def test_too_long(self):
        is_valid, error = validate_username("a" * 31)
        assert is_valid is False
        assert "not exceed 30" in error

    def test_empty_username(self):
        is_valid, error = validate_username("")
        assert is_valid is False
        assert "required" in error

    def test_invalid_characters_space(self):
        is_valid, error = validate_username("john doe")
        assert is_valid is False
        assert "letters, digits, underscores, or hyphens" in error

    def test_invalid_characters_special(self):
        is_valid, error = validate_username("user@name")
        assert is_valid is False
        assert "letters, digits, underscores, or hyphens" in error

    def test_invalid_characters_dot(self):
        is_valid, error = validate_username("user.name")
        assert is_valid is False


class TestSanitizeInput:
    """Tests for the sanitize_input function."""

    def test_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_strips_tabs_and_newlines(self):
        assert sanitize_input("\thello\n") == "hello"

    def test_plain_text_passes_through(self):
        assert sanitize_input("Hello, world!") == "Hello, world!"

    def test_rejects_script_tag(self):
        with pytest.raises(ValueError, match="unescaped HTML tags"):
            sanitize_input("<script>alert('xss')</script>")

    def test_rejects_div_tag(self):
        with pytest.raises(ValueError, match="unescaped HTML tags"):
            sanitize_input("<div>content</div>")

    def test_rejects_img_tag(self):
        with pytest.raises(ValueError, match="unescaped HTML tags"):
            sanitize_input('<img src="x" onerror="alert(1)">')

    def test_rejects_closing_tag(self):
        with pytest.raises(ValueError, match="unescaped HTML tags"):
            sanitize_input("some text</script>")

    def test_allows_escaped_entities(self):
        result = sanitize_input("&lt;script&gt;")
        assert result == "&lt;script&gt;"

    def test_allows_angle_brackets_without_tag(self):
        result = sanitize_input("5 < 10 and 10 > 5")
        assert result == "5 < 10 and 10 > 5"

    def test_allows_math_expressions(self):
        result = sanitize_input("a < b")
        assert result == "a < b"

    def test_rejects_tag_after_stripping(self):
        with pytest.raises(ValueError, match="unescaped HTML tags"):
            sanitize_input("  <script>alert('xss')</script>  ")
