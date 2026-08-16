"""Property-based tests for slug generation.

Validates: Requirements 3.3
"""

import string

from hypothesis import given, settings, assume
from hypothesis.strategies import text, lists

from app.utils import generate_slug


# Feature: personal-blog, Property 1: Slug generation produces valid URL-safe strings
class TestSlugValidCharacters:
    """Property 1: Slug generation produces valid URL-safe strings."""

    @settings(max_examples=100)
    @given(title=text(min_size=1, alphabet=string.ascii_letters + string.digits + " "))
    def test_slug_contains_only_valid_characters(self, title):
        """**Validates: Requirements 3.3**

        For any string used as a post title, the generate_slug function SHALL
        produce a string that contains only lowercase letters, digits, and hyphens.
        """
        slug = generate_slug(title)
        assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in slug)

    @settings(max_examples=100)
    @given(title=text(min_size=1, alphabet=string.ascii_letters + string.digits + " "))
    def test_slug_does_not_start_or_end_with_hyphen(self, title):
        """**Validates: Requirements 3.3**

        For any string used as a post title, the generate_slug function SHALL
        produce a string that does not start or end with a hyphen.
        """
        slug = generate_slug(title)
        if slug:
            assert slug[0] != "-"
            assert slug[-1] != "-"

    @settings(max_examples=100)
    @given(title=text(min_size=1, alphabet=string.ascii_letters + string.digits + " "))
    def test_slug_contains_no_consecutive_hyphens(self, title):
        """**Validates: Requirements 3.3**

        For any string used as a post title, the generate_slug function SHALL
        produce a string that contains no consecutive hyphens.
        """
        slug = generate_slug(title)
        assert "--" not in slug

    @settings(max_examples=100)
    @given(title=text(min_size=1, alphabet=string.ascii_letters + string.digits))
    def test_slug_is_non_empty_for_alphanumeric_title(self, title):
        """**Validates: Requirements 3.3**

        For any title with at least one alphanumeric character, the generate_slug
        function SHALL produce a non-empty string.
        """
        slug = generate_slug(title)
        assert len(slug) > 0

    @settings(max_examples=100)
    @given(title=text(min_size=1))
    def test_slug_valid_with_arbitrary_unicode(self, title):
        """**Validates: Requirements 3.3**

        For any arbitrary string title, the slug SHALL only contain valid characters,
        have no leading/trailing hyphens, and no consecutive hyphens.
        """
        slug = generate_slug(title)
        assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in slug)
        if slug:
            assert slug[0] != "-"
            assert slug[-1] != "-"
            assert "--" not in slug


# Feature: personal-blog, Property 2: Slug uniqueness with suffix
class TestSlugUniqueness:
    """Property 2: Slug uniqueness with suffix."""

    @settings(max_examples=100)
    @given(
        title=text(min_size=1, alphabet=string.ascii_letters + string.digits + " "),
        suffix_count=lists(
            text(min_size=1, alphabet=string.ascii_letters + string.digits + " "),
            min_size=0,
            max_size=5,
        ),
    )
    def test_slug_unique_when_collision_exists(self, title, suffix_count):
        """**Validates: Requirements 3.3**

        For any title that generates a slug already present in an existing set of
        slugs, the generate_slug function SHALL produce a unique slug by appending
        a numeric suffix such that the result is not in the existing set.
        """
        # Generate the base slug first
        base_slug = generate_slug(title)
        assume(base_slug != "")

        # Build existing_slugs that includes the base slug to force collision
        existing_slugs = [base_slug]
        # Add some suffixed variants to force higher suffixes
        for i in range(len(suffix_count)):
            existing_slugs.append(f"{base_slug}-{i + 1}")

        # Generate with collision - result must not be in existing set
        result = generate_slug(title, existing_slugs)
        assert result not in existing_slugs

    @settings(max_examples=100)
    @given(title=text(min_size=1, alphabet=string.ascii_letters + string.digits + " "))
    def test_slug_no_suffix_when_no_collision(self, title):
        """**Validates: Requirements 3.3**

        When no collision exists, generate_slug SHALL return the base slug
        without any numeric suffix.
        """
        base_slug = generate_slug(title)
        assume(base_slug != "")

        # Use an empty list - no collision possible
        result = generate_slug(title, [])
        assert result == base_slug

    @settings(max_examples=100)
    @given(title=text(min_size=1, alphabet=string.ascii_letters + string.digits + " "))
    def test_slug_with_suffix_is_still_valid(self, title):
        """**Validates: Requirements 3.3**

        When a suffix is appended for uniqueness, the resulting slug SHALL still
        contain only valid URL-safe characters.
        """
        base_slug = generate_slug(title)
        assume(base_slug != "")

        # Force collision
        existing_slugs = [base_slug]
        result = generate_slug(title, existing_slugs)

        # Validate the suffixed slug still meets all URL-safe criteria
        assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in result)
        assert result[0] != "-"
        assert result[-1] != "-"
        assert "--" not in result
