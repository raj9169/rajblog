"""Tests for custom error pages and error handling.

Validates Requirements 9.1-9.4, 13.5:
- Custom 404 page for non-existent routes (HTML)
- Custom 403 page for forbidden access (HTML)
- Custom 500 page for internal server errors (HTML)
- API endpoints return JSON error format
- No stack trace exposed in error responses
"""

import pytest

from app.extensions import db
from app.models.post import Post
from app.models.user import User


@pytest.fixture
def user(app):
    """Create a user for testing."""
    u = User(username='erroruser', email='error@example.com')
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
    """Authenticated test client."""
    client.post('/login', data={
        'email': 'error@example.com',
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
def sample_post(app, user):
    """Create a published post owned by user."""
    post = Post(
        title='Error Test Post',
        slug='error-test-post',
        content='Content for error testing.',
        author_id=user.id,
        status='published',
    )
    db.session.add(post)
    db.session.commit()
    return post


class TestCustom404Page:
    """Tests for custom 404 Not Found error page."""

    def test_nonexistent_route_returns_404(self, client):
        """Non-existent URL returns 404 status code."""
        response = client.get('/this-route-does-not-exist')
        assert response.status_code == 404

    def test_404_page_uses_custom_template(self, client):
        """404 page contains custom content, not a default server page."""
        response = client.get('/this-route-does-not-exist')
        assert response.status_code == 404
        assert b'404' in response.data
        assert b'Page Not Found' in response.data

    def test_404_page_has_home_link(self, client):
        """404 page includes a link back to the home page."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        assert b'Back to Home' in response.data

    def test_404_page_uses_base_template(self, client):
        """404 page extends the base template (has navigation)."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        # Base template includes navigation with Home link
        assert b'nav' in response.data

    def test_nonexistent_post_slug_returns_404(self, client):
        """Accessing a non-existent post slug returns 404."""
        response = client.get('/post/this-slug-does-not-exist')
        assert response.status_code == 404


class TestCustom403Page:
    """Tests for custom 403 Forbidden error page."""

    def test_forbidden_returns_403_with_custom_page(self, other_auth_client, sample_post):
        """403 Forbidden returns custom error page."""
        response = other_auth_client.get(f'/post/{sample_post.slug}/edit')
        assert response.status_code == 403
        assert b'403' in response.data
        assert b'Forbidden' in response.data

    def test_403_page_has_home_link(self, other_auth_client, sample_post):
        """403 page includes a link back to the home page."""
        response = other_auth_client.get(f'/post/{sample_post.slug}/edit')
        assert response.status_code == 403
        assert b'Back to Home' in response.data

    def test_403_page_uses_base_template(self, other_auth_client, sample_post):
        """403 page extends the base template (has navigation)."""
        response = other_auth_client.get(f'/post/{sample_post.slug}/edit')
        assert response.status_code == 403
        assert b'nav' in response.data


class TestCustom500Page:
    """Tests for custom 500 Internal Server Error page."""

    def test_500_returns_custom_page(self, app):
        """500 error returns a custom error page without stack traces."""
        # Disable exception propagation so the error handler runs
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = False

        @app.route('/trigger-500')
        def trigger_500():
            raise RuntimeError('Deliberate test error')

        with app.test_client() as c:
            response = c.get('/trigger-500')
            assert response.status_code == 500
            assert b'500' in response.data
            assert b'Internal Server Error' in response.data

    def test_500_page_has_home_link(self, app):
        """500 page includes a link back to the home page."""
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = False

        @app.route('/trigger-500-link')
        def trigger_500_link():
            raise RuntimeError('Deliberate test error for link check')

        with app.test_client() as c:
            response = c.get('/trigger-500-link')
            assert response.status_code == 500
            assert b'Back to Home' in response.data

    def test_500_no_stack_trace_exposed(self, app):
        """500 response does not expose stack traces or internal paths."""
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = False

        @app.route('/trigger-500-trace')
        def trigger_500_trace():
            raise RuntimeError('Secret error details should not be shown')

        with app.test_client() as c:
            response = c.get('/trigger-500-trace')
            assert response.status_code == 500
            body = response.data.decode()
            assert 'Traceback' not in body
            assert 'RuntimeError' not in body
            assert 'Secret error details should not be shown' not in body

    def test_500_page_uses_base_template(self, app):
        """500 page extends the base template (has navigation)."""
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = False

        @app.route('/trigger-500-nav')
        def trigger_500_nav():
            raise RuntimeError('Test error for nav check')

        with app.test_client() as c:
            response = c.get('/trigger-500-nav')
            assert response.status_code == 500
            assert b'nav' in response.data


class TestAPIErrorResponses:
    """Tests for JSON error responses from API endpoints."""

    def test_api_404_returns_json(self, client):
        """API 404 returns JSON error format, not HTML."""
        response = client.get('/api/posts/99999')
        assert response.status_code == 404
        data = response.get_json()
        assert data is not None
        assert 'error' in data

    def test_api_nonexistent_route_returns_json_404(self, client):
        """Non-existent API route returns JSON 404."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert data is not None
        assert 'error' in data

    def test_api_403_returns_json(self, other_auth_client, sample_post):
        """API 403 returns JSON error format."""
        response = other_auth_client.put(
            f'/api/posts/{sample_post.id}',
            json={'title': 'Hacked'},
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data is not None
        assert 'error' in data

    def test_api_401_returns_json(self, client):
        """API 401 returns JSON error format for unauthenticated requests."""
        response = client.post('/api/posts', json={
            'title': 'Test',
            'content': 'Content',
        })
        assert response.status_code == 401
        data = response.get_json()
        assert data is not None
        assert 'error' in data

    def test_api_500_returns_json(self, app):
        """API 500 returns JSON error format without stack traces."""
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = False

        @app.route('/api/trigger-500')
        def api_trigger_500():
            raise RuntimeError('API internal error')

        with app.test_client() as c:
            response = c.get('/api/trigger-500')
            assert response.status_code == 500
            data = response.get_json()
            assert data is not None
            assert 'error' in data
            assert 'Traceback' not in str(data)
            assert 'RuntimeError' not in str(data)
