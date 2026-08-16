"""Utility functions for slug generation, validation, and input sanitization."""

import re


def generate_slug(title: str, existing_slugs: list[str] | None = None) -> str:
    """
    Generate a URL-friendly slug from a post title.

    Algorithm:
    1. Convert to lowercase
    2. Replace spaces and consecutive whitespace with single hyphen
    3. Remove characters that are not lowercase letters, digits, or hyphens
    4. Collapse consecutive hyphens into a single hyphen
    5. Trim leading/trailing hyphens
    6. If slug exists in existing_slugs, append numeric suffix (-1, -2, ...)

    Args:
        title: The post title to slugify.
        existing_slugs: List of slugs already in use (for deduplication).

    Returns:
        A unique, URL-friendly slug string.
    """
    if existing_slugs is None:
        existing_slugs = []

    # Step 1: Convert to lowercase
    slug = title.lower()

    # Step 2: Replace whitespace (spaces, tabs, newlines, etc.) with a single hyphen
    slug = re.sub(r'\s+', '-', slug)

    # Step 3: Remove characters that are not lowercase letters, digits, or hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # Step 4: Collapse consecutive hyphens into a single hyphen
    slug = re.sub(r'-+', '-', slug)

    # Step 5: Trim leading/trailing hyphens
    slug = slug.strip('-')

    # Step 6: Ensure uniqueness by appending numeric suffix if needed
    if slug not in existing_slugs:
        return slug

    counter = 1
    while f"{slug}-{counter}" in existing_slugs:
        counter += 1
    return f"{slug}-{counter}"


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Rules:
    - Must contain exactly one @ character
    - The domain part (after @) must contain at least one dot
    - Total length must not exceed 254 characters

    Args:
        email: The email address to validate.

    Returns:
        True if the email is valid, False otherwise.
    """
    if not email or len(email) > 254:
        return False

    # Must contain exactly one @
    if email.count('@') != 1:
        return False

    local, domain = email.split('@')

    # Local part must not be empty
    if not local:
        return False

    # Domain must not be empty and must contain at least one dot
    if not domain or '.' not in domain:
        return False

    # Domain must not start or end with a dot, and no consecutive dots
    if domain.startswith('.') or domain.endswith('.'):
        return False

    return True


def validate_username(username: str) -> tuple[bool, str | None]:
    """
    Validate username format.

    Rules:
    - Must be between 3 and 30 characters (inclusive)
    - Must contain only letters (a-zA-Z), digits (0-9), underscores (_), or hyphens (-)

    Args:
        username: The username to validate.

    Returns:
        A tuple of (is_valid, error_message). error_message is None if valid.
    """
    if not username:
        return False, "Username is required."

    if len(username) < 3:
        return False, "Username must be at least 3 characters long."

    if len(username) > 30:
        return False, "Username must not exceed 30 characters."

    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username may only contain letters, digits, underscores, or hyphens."

    return True, None


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by stripping whitespace and rejecting unescaped HTML tags.

    Rules:
    - Strip leading and trailing whitespace
    - Raise ValueError if the text contains unescaped HTML tags (e.g., <script>, <div>)

    Args:
        text: The input text to sanitize.

    Returns:
        The sanitized (stripped) text.

    Raises:
        ValueError: If the text contains unescaped HTML tags.
    """
    stripped = text.strip()

    # Detect unescaped HTML tags: matches < followed by optional /, then a letter,
    # then any characters until >
    if re.search(r'</?[a-zA-Z][^>]*>', stripped):
        raise ValueError("Input contains unescaped HTML tags.")

    return stripped
