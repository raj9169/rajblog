"""Unit tests for REST API endpoints.

Tests cover all CRUD operations for posts and comments, including
error responses for 400, 401, 403, and 404 status codes.
Validates Requirements 7.1-7.11, 13.4, 13.5.
"""

import pytest

from app.extensions import db
from app.models.post import Post
from app.models.user import User


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def user(app):
    """Create a test user."""
    u = User(username='testuser', email='test@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def other_user(app):
    """Create a second test user (non-owner)."""
    u = User(username='otheruser', email='other@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth_client(client, user):
    """Authenticated test client (logged in as user)."""
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123',
    })
    return client


@pytest.fixture
def other_auth_client(app, other_user):
    """Authenticated test client logged in as other_user."""
    c = app.test_client()
    c.post('/login', data={
        'email': 'other@example.com',
        'password': 'password123',
    })
    return c


@pytest.fixture
def published_post(app, user):
    """Create a published post owned by user."""
    post = Post(
        title='Published Post',
        slug='published-post',
        content='This is a published blog post with some content.',
        author_id=user.id,
        status='published',
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture
def draft_post(app, user):
    """Create a draft post owned by user."""
    post = Post(
        title='Draft Post',
        slug='draft-post',
        content='This is a draft blog post.',
        author_id=user.id,
        status='draft',
    )
    db.session.add(post)
    db.session.commit()
    return post


# ─── GET /api/posts ──────────────────────────────────────────────────────────


class TestGetPosts:
    """Tests for GET /api/posts endpoint."""

    def test_returns_only_published_posts(self, client, published_post, draft_post):
        """Only published posts appear in the listing."""
        resp = client.get('/api/posts')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]['title'] == 'Published Post'

    def test_returns_correct_fields(self, client, published_post):
        """Response contains expected fields with content_excerpt (not full content)."""
        resp = client.get('/api/posts')
        data = resp.get_json()
        post_data = data[0]
        assert 'id' in post_data
        assert 'title' in post_data
        assert 'slug' in post_data
        assert 'content_excerpt' in post_data
        assert 'author' in post_data
        assert 'created_at' in post_data
        # Full content should NOT be in the listing
        assert 'content' not in post_data

    def test_empty_when_no_published_posts(self, client, draft_post):
        """Returns empty array when all posts are drafts."""
        resp = client.get('/api/posts')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == []

    def test_author_field_is_username(self, client, published_post):
        """Author field is the username string."""
        resp = client.get('/api/posts')
        data = resp.get_json()
        assert data[0]['author'] == 'testuser'


# ─── GET /api/posts/<id> ─────────────────────────────────────────────────────


class TestGetPostById:
    """Tests for GET /api/posts/<id> endpoint."""

    def test_returns_full_post(self, client, published_post):
        """Returns full post detail with content field."""
        resp = client.get(f'/api/posts/{published_post.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == published_post.id
        assert data['title'] == 'Published Post'
        assert data['slug'] == 'published-post'
        assert data['content'] == published_post.content
        assert data['author'] == 'testuser'
        assert data['status'] == 'published'
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_returns_404_for_nonexistent(self, client):
        """Returns 404 JSON for non-existent post ID."""
        resp = client.get('/api/posts/9999')
        assert resp.status_code == 404
        data = resp.get_json()
        assert 'error' in data


# ─── POST /api/posts ─────────────────────────────────────────────────────────


class TestCreatePost:
    """Tests for POST /api/posts endpoint."""

    def test_authenticated_creates_post(self, auth_client):
        """Authenticated user can create a post (201)."""
        resp = auth_client.post('/api/posts', json={
            'title': 'New Post',
            'content': 'This is the content of the new post.',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['title'] == 'New Post'
        assert data['content'] == 'This is the content of the new post.'
        assert data['status'] == 'draft'
        assert data['author'] == 'testuser'
        assert 'id' in data
        assert 'slug' in data

    def test_unauthenticated_gets_401(self, client):
        """Unauthenticated request returns 401."""
        resp = client.post('/api/posts', json={
            'title': 'New Post',
            'content': 'Content here.',
        })
        assert resp.status_code == 401
        data = resp.get_json()
        assert 'error' in data

    def test_empty_title_gets_400(self, auth_client):
        """Empty title returns 400 validation error."""
        resp = auth_client.post('/api/posts', json={
            'title': '',
            'content': 'Some content.',
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_empty_content_gets_400(self, auth_client):
        """Empty content returns 400 validation error."""
        resp = auth_client.post('/api/posts', json={
            'title': 'A Title',
            'content': '',
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_no_json_body_gets_400(self, auth_client):
        """Request without JSON body returns 400."""
        resp = auth_client.post('/api/posts', data='not json',
                                content_type='text/plain')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data


# ─── PUT /api/posts/<id> ─────────────────────────────────────────────────────


class TestUpdatePost:
    """Tests for PUT /api/posts/<id> endpoint."""

    def test_owner_can_update(self, auth_client, published_post):
        """Owner can update their post (200)."""
        resp = auth_client.put(f'/api/posts/{published_post.id}', json={
            'title': 'Updated Title',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['title'] == 'Updated Title'

    def test_non_owner_gets_403(self, other_auth_client, published_post):
        """Non-owner gets 403 Forbidden."""
        resp = other_auth_client.put(f'/api/posts/{published_post.id}', json={
            'title': 'Hacked Title',
        })
        assert resp.status_code == 403
        data = resp.get_json()
        assert 'error' in data

    def test_unauthenticated_gets_401(self, client, published_post):
        """Unauthenticated request returns 401."""
        resp = client.put(f'/api/posts/{published_post.id}', json={
            'title': 'New Title',
        })
        assert resp.status_code == 401
        data = resp.get_json()
        assert 'error' in data

    def test_nonexistent_gets_404(self, auth_client):
        """Non-existent post returns 404."""
        resp = auth_client.put('/api/posts/9999', json={
            'title': 'Title',
        })
        assert resp.status_code == 404
        data = resp.get_json()
        assert 'error' in data

    def test_empty_title_gets_400(self, auth_client, published_post):
        """Empty title in update returns 400."""
        resp = auth_client.put(f'/api/posts/{published_post.id}', json={
            'title': '',
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_empty_content_gets_400(self, auth_client, published_post):
        """Empty content in update returns 400."""
        resp = auth_client.put(f'/api/posts/{published_post.id}', json={
            'content': '',
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data


# ─── DELETE /api/posts/<id> ──────────────────────────────────────────────────


class TestDeletePost:
    """Tests for DELETE /api/posts/<id> endpoint."""

    def test_owner_can_delete(self, auth_client, published_post):
        """Owner can delete their post (204)."""
        resp = auth_client.delete(f'/api/posts/{published_post.id}')
        assert resp.status_code == 204

    def test_non_owner_gets_403(self, other_auth_client, published_post):
        """Non-owner gets 403 Forbidden."""
        resp = other_auth_client.delete(f'/api/posts/{published_post.id}')
        assert resp.status_code == 403
        data = resp.get_json()
        assert 'error' in data

    def test_unauthenticated_gets_401(self, client, published_post):
        """Unauthenticated request returns 401."""
        resp = client.delete(f'/api/posts/{published_post.id}')
        assert resp.status_code == 401
        data = resp.get_json()
        assert 'error' in data

    def test_nonexistent_gets_404(self, auth_client):
        """Non-existent post returns 404."""
        resp = auth_client.delete('/api/posts/9999')
        assert resp.status_code == 404
        data = resp.get_json()
        assert 'error' in data


# ─── POST /api/posts/<id>/comments ───────────────────────────────────────────


class TestCreateComment:
    """Tests for POST /api/posts/<id>/comments endpoint."""

    def test_authenticated_creates_comment(self, auth_client, published_post):
        """Authenticated user can create a comment (201)."""
        resp = auth_client.post(f'/api/posts/{published_post.id}/comments', json={
            'content': 'Great post!',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['content'] == 'Great post!'
        assert data['author'] == 'testuser'
        assert data['post_id'] == published_post.id
        assert 'id' in data
        assert 'created_at' in data

    def test_unauthenticated_gets_401(self, client, published_post):
        """Unauthenticated request returns 401."""
        resp = client.post(f'/api/posts/{published_post.id}/comments', json={
            'content': 'A comment.',
        })
        assert resp.status_code == 401
        data = resp.get_json()
        assert 'error' in data

    def test_nonexistent_post_gets_404(self, auth_client):
        """Comment on non-existent post returns 404."""
        resp = auth_client.post('/api/posts/9999/comments', json={
            'content': 'A comment.',
        })
        assert resp.status_code == 404
        data = resp.get_json()
        assert 'error' in data

    def test_empty_content_gets_400(self, auth_client, published_post):
        """Empty comment content returns 400."""
        resp = auth_client.post(f'/api/posts/{published_post.id}/comments', json={
            'content': '',
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
