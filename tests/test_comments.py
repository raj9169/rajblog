"""Tests for comment creation, validation, and display."""

import pytest

from app.extensions import db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User


@pytest.fixture
def user(app):
    """Create a user for testing."""
    u = User(username='commenter', email='commenter@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def other_user(app):
    """Create a second user for comment authoring."""
    u = User(username='otheruser', email='other@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth_client(client, user):
    """Authenticated test client logged in as 'commenter'."""
    client.post('/login', data={
        'email': 'commenter@example.com',
        'password': 'password123',
    })
    return client


@pytest.fixture
def published_post(app, user):
    """Create a published post for comment tests."""
    post = Post(
        title='Comment Target',
        slug='comment-target',
        content='Post content for testing comments.',
        author_id=user.id,
        status='published',
    )
    db.session.add(post)
    db.session.commit()
    return post


class TestCommentCreation:
    """Tests for POST /post/<slug>/comment."""

    def test_valid_comment_created(self, auth_client, published_post, user):
        """Valid comment submission creates a comment record."""
        response = auth_client.post(
            f'/post/{published_post.slug}/comment',
            data={'content': 'Great post!'},
            follow_redirects=False,
        )
        assert response.status_code == 302

        comment = Comment.query.filter_by(post_id=published_post.id).first()
        assert comment is not None
        assert comment.content == 'Great post!'
        assert comment.author_id == user.id

    def test_comment_content_trimmed(self, auth_client, published_post):
        """Leading and trailing whitespace is trimmed from comment content."""
        auth_client.post(
            f'/post/{published_post.slug}/comment',
            data={'content': '   Hello world!   '},
            follow_redirects=True,
        )
        comment = Comment.query.filter_by(post_id=published_post.id).first()
        assert comment is not None
        assert comment.content == 'Hello world!'

    def test_empty_content_rejected(self, auth_client, published_post):
        """Empty comment content is rejected with validation error."""
        response = auth_client.post(
            f'/post/{published_post.slug}/comment',
            data={'content': ''},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert Comment.query.filter_by(post_id=published_post.id).count() == 0

    def test_whitespace_only_rejected(self, auth_client, published_post):
        """Whitespace-only comment content is rejected."""
        response = auth_client.post(
            f'/post/{published_post.slug}/comment',
            data={'content': '    \t\n   '},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert Comment.query.filter_by(post_id=published_post.id).count() == 0

    def test_too_long_content_rejected(self, auth_client, published_post):
        """Comment content exceeding 2000 characters is rejected."""
        long_content = 'x' * 2001
        response = auth_client.post(
            f'/post/{published_post.slug}/comment',
            data={'content': long_content},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert Comment.query.filter_by(post_id=published_post.id).count() == 0

    def test_exactly_2000_chars_accepted(self, auth_client, published_post):
        """Comment at exactly 2000 characters is accepted."""
        content = 'a' * 2000
        auth_client.post(
            f'/post/{published_post.slug}/comment',
            data={'content': content},
            follow_redirects=True,
        )
        comment = Comment.query.filter_by(post_id=published_post.id).first()
        assert comment is not None
        assert len(comment.content) == 2000

    def test_unauthenticated_cannot_comment(self, client, published_post):
        """Unauthenticated user is redirected when trying to comment."""
        response = client.post(
            f'/post/{published_post.slug}/comment',
            data={'content': 'Should not work.'},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
        assert Comment.query.filter_by(post_id=published_post.id).count() == 0

    def test_comment_on_nonexistent_post_404(self, auth_client):
        """Commenting on a non-existent post returns 404."""
        response = auth_client.post(
            '/post/no-such-post/comment',
            data={'content': 'Hello!'},
        )
        assert response.status_code == 404


class TestCommentDisplay:
    """Tests for comment display ordering on post detail."""

    def test_comments_ordered_ascending(self, client, published_post, user, app):
        """Comments are displayed in ascending created_at order."""
        from datetime import datetime, timedelta

        c1 = Comment(
            content='First comment',
            author_id=user.id,
            post_id=published_post.id,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
        )
        c2 = Comment(
            content='Second comment',
            author_id=user.id,
            post_id=published_post.id,
            created_at=datetime(2024, 1, 1, 11, 0, 0),
        )
        db.session.add_all([c1, c2])
        db.session.commit()

        response = client.get(f'/post/{published_post.slug}')
        assert response.status_code == 200
        data = response.data.decode()
        # First comment should appear before second in the rendered page
        assert data.index('First comment') < data.index('Second comment')

    def test_no_comments_message(self, client, published_post):
        """Post with no comments shows 'No comments yet' message."""
        response = client.get(f'/post/{published_post.slug}')
        assert response.status_code == 200
        assert b'No comments yet' in response.data
