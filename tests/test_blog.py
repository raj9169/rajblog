"""Tests for blog post management routes (CRUD, dashboard, profile)."""

import pytest

from app.extensions import db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User


@pytest.fixture
def user(app):
    """Create a user for testing."""
    u = User(username='author', email='author@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def other_user(app):
    """Create a second user for authorization tests."""
    u = User(username='otheruser', email='other@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def auth_client(client, user):
    """Authenticated test client logged in as 'author'."""
    client.post('/login', data={
        'email': 'author@example.com',
        'password': 'password123',
    })
    return client


@pytest.fixture
def other_auth_client(app, other_user):
    """Authenticated test client logged in as 'otheruser'."""
    c = app.test_client()
    c.post('/login', data={
        'email': 'other@example.com',
        'password': 'password123',
    })
    return c


@pytest.fixture
def sample_post(app, user):
    """Create a published sample post owned by 'author'."""
    post = Post(
        title='Test Post',
        slug='test-post',
        content='This is test content.',
        author_id=user.id,
        status='published',
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture
def draft_post(app, user):
    """Create a draft post owned by 'author'."""
    post = Post(
        title='Draft Post',
        slug='draft-post',
        content='Draft content here.',
        author_id=user.id,
        status='draft',
    )
    db.session.add(post)
    db.session.commit()
    return post


class TestPostCreation:
    """Tests for POST /post/new."""

    def test_create_post_success(self, auth_client, user):
        """Valid data creates a post and redirects to detail page."""
        response = auth_client.post('/post/new', data={
            'title': 'My New Post',
            'content': 'Some great content here.',
            'status': 'draft',
        }, follow_redirects=False)
        assert response.status_code == 302

        post = Post.query.filter_by(title='My New Post').first()
        assert post is not None
        assert post.slug == 'my-new-post'
        assert post.author_id == user.id
        assert post.status == 'draft'

    def test_create_post_published(self, auth_client):
        """Post can be created with published status."""
        response = auth_client.post('/post/new', data={
            'title': 'Published Post',
            'content': 'Content for published post.',
            'status': 'published',
        }, follow_redirects=False)
        assert response.status_code == 302

        post = Post.query.filter_by(title='Published Post').first()
        assert post is not None
        assert post.status == 'published'

    def test_create_post_empty_title(self, auth_client):
        """Empty title re-renders the form (no post created)."""
        response = auth_client.post('/post/new', data={
            'title': '',
            'content': 'Some content.',
            'status': 'draft',
        })
        assert response.status_code == 200
        assert Post.query.count() == 0

    def test_create_post_empty_content(self, auth_client):
        """Empty content re-renders the form (no post created)."""
        response = auth_client.post('/post/new', data={
            'title': 'Valid Title',
            'content': '',
            'status': 'draft',
        })
        assert response.status_code == 200
        assert Post.query.count() == 0

    def test_create_post_requires_auth(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get('/post/new', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_create_post_slug_auto_generation(self, auth_client):
        """Slug is auto-generated from title."""
        auth_client.post('/post/new', data={
            'title': 'Hello World Today',
            'content': 'Content.',
            'status': 'draft',
        })
        post = Post.query.first()
        assert post.slug == 'hello-world-today'

    def test_create_post_duplicate_slug_gets_suffix(self, auth_client, sample_post):
        """Duplicate slug gets numeric suffix appended."""
        auth_client.post('/post/new', data={
            'title': 'Test Post',
            'content': 'Different content.',
            'status': 'draft',
        })
        posts = Post.query.filter(Post.slug.like('test-post%')).all()
        slugs = [p.slug for p in posts]
        assert 'test-post' in slugs
        assert 'test-post-1' in slugs


class TestPostEditing:
    """Tests for GET/POST /post/<slug>/edit."""

    def test_edit_post_form_prepopulated(self, auth_client, sample_post):
        """Edit form displays current post data."""
        response = auth_client.get(f'/post/{sample_post.slug}/edit')
        assert response.status_code == 200
        assert b'Test Post' in response.data
        assert b'This is test content.' in response.data

    def test_edit_post_success(self, auth_client, sample_post):
        """Owner can update post title, content, and status."""
        response = auth_client.post(f'/post/{sample_post.slug}/edit', data={
            'title': 'Updated Title',
            'content': 'Updated content.',
            'status': 'published',
        }, follow_redirects=False)
        assert response.status_code == 302

        db.session.refresh(sample_post)
        assert sample_post.title == 'Updated Title'
        assert sample_post.content == 'Updated content.'
        assert sample_post.status == 'published'

    def test_edit_post_non_owner_forbidden(self, other_auth_client, sample_post):
        """Non-owner gets 403 when trying to edit."""
        response = other_auth_client.get(f'/post/{sample_post.slug}/edit')
        assert response.status_code == 403

    def test_edit_post_non_owner_post_forbidden(self, other_auth_client, sample_post):
        """Non-owner gets 403 when submitting edit form."""
        response = other_auth_client.post(f'/post/{sample_post.slug}/edit', data={
            'title': 'Hacked',
            'content': 'Hacked content.',
            'status': 'published',
        })
        assert response.status_code == 403

    def test_edit_nonexistent_post_404(self, auth_client):
        """Editing a non-existent post returns 404."""
        response = auth_client.get('/post/nonexistent-slug/edit')
        assert response.status_code == 404


class TestPostDeletion:
    """Tests for POST /post/<slug>/delete."""

    def test_delete_post_success(self, auth_client, sample_post):
        """Owner can delete their post."""
        response = auth_client.post(
            f'/post/{sample_post.slug}/delete', follow_redirects=False
        )
        assert response.status_code == 302
        assert Post.query.filter_by(slug='test-post').first() is None

    def test_delete_post_non_owner_forbidden(self, other_auth_client, sample_post):
        """Non-owner gets 403 when trying to delete."""
        response = other_auth_client.post(f'/post/{sample_post.slug}/delete')
        assert response.status_code == 403
        # Post still exists
        assert Post.query.filter_by(slug='test-post').first() is not None

    def test_delete_post_cascades_comments(self, auth_client, sample_post, user):
        """Deleting a post also deletes its comments."""
        comment = Comment(
            content='A comment.',
            author_id=user.id,
            post_id=sample_post.id,
        )
        db.session.add(comment)
        db.session.commit()
        comment_id = comment.id

        auth_client.post(f'/post/{sample_post.slug}/delete')
        assert db.session.get(Comment, comment_id) is None

    def test_delete_nonexistent_post_404(self, auth_client):
        """Deleting a non-existent post returns 404."""
        response = auth_client.post('/post/no-such-post/delete')
        assert response.status_code == 404


class TestPostDetail:
    """Tests for GET /post/<slug>."""

    def test_published_post_visible_to_all(self, client, sample_post):
        """Published posts are visible to unauthenticated users."""
        response = client.get(f'/post/{sample_post.slug}')
        assert response.status_code == 200
        assert b'Test Post' in response.data
        assert b'This is test content.' in response.data

    def test_draft_visible_to_author(self, auth_client, draft_post):
        """Draft posts are visible to their author."""
        response = auth_client.get(f'/post/{draft_post.slug}')
        assert response.status_code == 200
        assert b'Draft Post' in response.data

    def test_draft_not_visible_to_other_user(self, other_auth_client, draft_post):
        """Draft posts return 404 for other authenticated users."""
        response = other_auth_client.get(f'/post/{draft_post.slug}')
        assert response.status_code == 404

    def test_draft_not_visible_to_anonymous(self, client, draft_post):
        """Draft posts return 404 for unauthenticated users."""
        response = client.get(f'/post/{draft_post.slug}')
        assert response.status_code == 404

    def test_nonexistent_post_returns_404(self, client):
        """Requesting a non-existent slug returns 404."""
        response = client.get('/post/does-not-exist')
        assert response.status_code == 404


class TestDashboard:
    """Tests for GET /dashboard."""

    def test_dashboard_shows_user_posts(self, auth_client, sample_post):
        """Dashboard displays user's posts."""
        response = auth_client.get('/dashboard')
        assert response.status_code == 200
        assert b'Test Post' in response.data

    def test_dashboard_shows_comment_count(self, auth_client, sample_post, user):
        """Dashboard shows comment count for each post."""
        comment = Comment(
            content='A comment.',
            author_id=user.id,
            post_id=sample_post.id,
        )
        db.session.add(comment)
        db.session.commit()

        response = auth_client.get('/dashboard')
        assert response.status_code == 200
        # The template renders post.comments.count() — should show "1"
        assert b'1' in response.data

    def test_dashboard_empty_state(self, auth_client):
        """Dashboard shows create link when user has no posts."""
        response = auth_client.get('/dashboard')
        assert response.status_code == 200
        assert b'Create your first post' in response.data

    def test_dashboard_requires_auth(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


class TestProfile:
    """Tests for GET /profile."""

    def test_profile_displays_user_info(self, auth_client, user):
        """Profile shows username, email, and join date."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'author' in response.data
        assert b'author@example.com' in response.data

    def test_profile_requires_auth(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get('/profile', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
