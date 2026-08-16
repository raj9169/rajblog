"""Property-based tests for public visibility invariant.

Property 6: Public visibility invariant

For any collection of Posts with mixed statuses ("draft" and "published"),
the public post listing and the GET /api/posts endpoint SHALL return only
Posts whose status is "published" — no draft Post SHALL appear in public results.

**Validates: Requirements 4.4, 4.5, 7.1**
"""

import os
import string

from hypothesis import given, settings, assume
from hypothesis.strategies import (
    composite,
    integers,
    lists,
    sampled_from,
    text,
)

# Set DATABASE_URI to sqlite before importing the app
os.environ.setdefault('DATABASE_URI', 'sqlite:///:memory:')

from app import create_app
from app.extensions import db as _db
from app.models.post import Post
from app.models.user import User


# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

TITLE_CHARS = string.ascii_letters + string.digits + " "
CONTENT_CHARS = string.ascii_letters + string.digits + " .,!?"


@composite
def post_data(draw):
    """Generate a (title, content, status) tuple for a post."""
    title = draw(text(alphabet=TITLE_CHARS, min_size=1, max_size=50))
    content = draw(text(alphabet=CONTENT_CHARS, min_size=1, max_size=200))
    status = draw(sampled_from(["draft", "published"]))
    return (title, content, status)


@composite
def post_list(draw):
    """Generate a list of post data with mixed statuses."""
    posts = draw(lists(post_data(), min_size=1, max_size=10))
    return posts


# --------------------------------------------------------------------------
# Test app setup
# --------------------------------------------------------------------------

_app = create_app('testing')
_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
_app.config['WTF_CSRF_ENABLED'] = False


# --------------------------------------------------------------------------
# Property 6: Public visibility invariant
# **Validates: Requirements 4.4, 4.5, 7.1**
# --------------------------------------------------------------------------


class TestPublicVisibilityInvariant:
    """Property 6: Public visibility invariant.

    For any collection of Posts with mixed statuses ("draft" and "published"),
    the public post listing and the GET /api/posts endpoint SHALL return only
    Posts whose status is "published" — no draft Post SHALL appear in public
    results.

    **Validates: Requirements 4.4, 4.5, 7.1**
    """

    @settings(max_examples=100)
    @given(posts_data=post_list())
    def test_api_posts_returns_only_published(self, posts_data):
        """**Validates: Requirements 4.4, 7.1**

        GET /api/posts SHALL return only posts with status "published".
        No draft post SHALL appear in the response.
        """
        with _app.app_context():
            _db.create_all()
            try:
                # Create a user for authoring posts
                user = User(
                    username='testuser',
                    email='test@example.com',
                    password_hash='fakehash',
                )
                _db.session.add(user)
                _db.session.commit()

                # Create posts with mixed statuses
                expected_published_count = 0
                for i, (title, content, status) in enumerate(posts_data):
                    post = Post(
                        title=title,
                        slug=f'slug-{i}',
                        content=content,
                        author_id=user.id,
                        status=status,
                    )
                    _db.session.add(post)
                    if status == 'published':
                        expected_published_count += 1
                _db.session.commit()

                # Query the API endpoint
                with _app.test_client() as client:
                    response = client.get('/api/posts')
                    assert response.status_code == 200
                    data = response.get_json()

                    # Only published posts should appear
                    assert len(data) == expected_published_count

                    # No draft should be present
                    for post_dict in data:
                        assert post_dict.get('status', 'published') != 'draft', (
                            "Draft post appeared in public API listing"
                        )
            finally:
                _db.session.remove()
                _db.drop_all()

    @settings(max_examples=100)
    @given(posts_data=post_list())
    def test_no_draft_slugs_in_public_listing(self, posts_data):
        """**Validates: Requirements 4.4, 4.5**

        The public listing SHALL exclude all draft posts — verified by
        checking that no slug from a draft post appears in the results.
        """
        with _app.app_context():
            _db.create_all()
            try:
                user = User(
                    username='testuser',
                    email='test@example.com',
                    password_hash='fakehash',
                )
                _db.session.add(user)
                _db.session.commit()

                draft_slugs = set()
                for i, (title, content, status) in enumerate(posts_data):
                    slug = f'slug-{i}'
                    post = Post(
                        title=title,
                        slug=slug,
                        content=content,
                        author_id=user.id,
                        status=status,
                    )
                    _db.session.add(post)
                    if status == 'draft':
                        draft_slugs.add(slug)
                _db.session.commit()

                with _app.test_client() as client:
                    response = client.get('/api/posts')
                    data = response.get_json()

                    returned_slugs = {p['slug'] for p in data}

                    # No draft slug should appear in the response
                    overlap = draft_slugs & returned_slugs
                    assert overlap == set(), (
                        f"Draft post slugs appeared in public listing: {overlap}"
                    )
            finally:
                _db.session.remove()
                _db.drop_all()
