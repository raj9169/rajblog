"""Property-based tests for post serialization completeness.

Property 8: Post serialization completeness

For any Post model instance, `post_to_dict(post, include_content=True)` SHALL
produce a dictionary containing exactly the keys: id, title, slug, content,
author, status, created_at, updated_at — with values matching the corresponding
model attributes.

**Validates: Requirements 7.1, 7.2**
"""

import os
import string
from datetime import datetime

from hypothesis import given, settings, assume
from hypothesis.strategies import (
    composite,
    integers,
    text,
)

# Set DATABASE_URI to sqlite before importing the app
os.environ.setdefault('DATABASE_URI', 'sqlite:///:memory:')

from app import create_app
from app.extensions import db as _db
from app.models.post import Post
from app.models.user import User
from app.api.routes import post_to_dict


# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

TITLE_CHARS = string.ascii_letters + string.digits + " "
SLUG_CHARS = string.ascii_lowercase + string.digits + "-"
CONTENT_CHARS = string.ascii_letters + string.digits + " .,!?\n"
USERNAME_CHARS = string.ascii_letters + string.digits + "_-"


@composite
def post_fields(draw):
    """Generate random fields for a Post model instance."""
    title = draw(text(alphabet=TITLE_CHARS, min_size=1, max_size=100))
    slug = draw(text(alphabet=SLUG_CHARS, min_size=1, max_size=50))
    # Ensure slug doesn't start/end with hyphen
    slug = slug.strip('-')
    if not slug:
        slug = 'test-slug'
    content = draw(text(alphabet=CONTENT_CHARS, min_size=1, max_size=500))
    return (title, slug, content)


# --------------------------------------------------------------------------
# Test app setup
# --------------------------------------------------------------------------

_app = create_app('testing')
_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
_app.config['WTF_CSRF_ENABLED'] = False


# --------------------------------------------------------------------------
# Property 8: Post serialization completeness
# **Validates: Requirements 7.1, 7.2**
# --------------------------------------------------------------------------


EXPECTED_KEYS_WITH_CONTENT = {
    'id', 'title', 'slug', 'content', 'author', 'status', 'created_at', 'updated_at'
}


class TestPostSerializationCompleteness:
    """Property 8: Post serialization completeness.

    For any Post model instance, `post_to_dict(post, include_content=True)` SHALL
    produce a dictionary containing exactly the keys: id, title, slug, content,
    author, status, created_at, updated_at — with values matching the corresponding
    model attributes.

    **Validates: Requirements 7.1, 7.2**
    """

    @settings(max_examples=100)
    @given(fields=post_fields())
    def test_post_to_dict_contains_exact_keys(self, fields):
        """**Validates: Requirements 7.1, 7.2**

        post_to_dict(post, include_content=True) SHALL produce a dictionary
        containing exactly the expected keys.
        """
        title, slug, content = fields

        with _app.app_context():
            _db.create_all()
            try:
                user = User(
                    username='author',
                    email='author@example.com',
                    password_hash='fakehash',
                )
                _db.session.add(user)
                _db.session.commit()

                post = Post(
                    title=title,
                    slug=slug,
                    content=content,
                    author_id=user.id,
                    status='published',
                )
                _db.session.add(post)
                _db.session.commit()

                result = post_to_dict(post, include_content=True)

                assert set(result.keys()) == EXPECTED_KEYS_WITH_CONTENT, (
                    f"Expected keys {EXPECTED_KEYS_WITH_CONTENT}, "
                    f"got {set(result.keys())}"
                )
            finally:
                _db.session.remove()
                _db.drop_all()

    @settings(max_examples=100)
    @given(fields=post_fields())
    def test_post_to_dict_values_match_model_attributes(self, fields):
        """**Validates: Requirements 7.1, 7.2**

        post_to_dict SHALL produce values matching the corresponding model
        attributes for each key.
        """
        title, slug, content = fields

        with _app.app_context():
            _db.create_all()
            try:
                user = User(
                    username='author',
                    email='author@example.com',
                    password_hash='fakehash',
                )
                _db.session.add(user)
                _db.session.commit()

                post = Post(
                    title=title,
                    slug=slug,
                    content=content,
                    author_id=user.id,
                    status='draft',
                )
                _db.session.add(post)
                _db.session.commit()

                result = post_to_dict(post, include_content=True)

                # Verify values match model attributes
                assert result['id'] == post.id
                assert result['title'] == post.title
                assert result['slug'] == post.slug
                assert result['content'] == post.content
                assert result['author'] == user.username
                assert result['status'] == post.status
                assert result['created_at'] == post.created_at.isoformat()
                assert result['updated_at'] == post.updated_at.isoformat()
            finally:
                _db.session.remove()
                _db.drop_all()

    @settings(max_examples=100)
    @given(fields=post_fields())
    def test_post_to_dict_status_preserved(self, fields):
        """**Validates: Requirements 7.2**

        post_to_dict SHALL correctly serialize both "draft" and "published"
        status values.
        """
        title, slug, content = fields

        with _app.app_context():
            _db.create_all()
            try:
                user = User(
                    username='author',
                    email='author@example.com',
                    password_hash='fakehash',
                )
                _db.session.add(user)
                _db.session.commit()

                # Test with "draft" status
                post_draft = Post(
                    title=title,
                    slug=slug + '-draft',
                    content=content,
                    author_id=user.id,
                    status='draft',
                )
                _db.session.add(post_draft)
                _db.session.commit()

                result_draft = post_to_dict(post_draft, include_content=True)
                assert result_draft['status'] == 'draft'

                # Test with "published" status
                post_pub = Post(
                    title=title,
                    slug=slug + '-pub',
                    content=content,
                    author_id=user.id,
                    status='published',
                )
                _db.session.add(post_pub)
                _db.session.commit()

                result_pub = post_to_dict(post_pub, include_content=True)
                assert result_pub['status'] == 'published'
            finally:
                _db.session.remove()
                _db.drop_all()
