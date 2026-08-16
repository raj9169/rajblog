"""Shared test fixtures."""

import os

import pytest

os.environ.setdefault('DATABASE_URI', 'sqlite:///:memory:')

from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.post import Post


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    """Provide the database session."""
    return _db


@pytest.fixture
def client(app):
    """Provide a test client."""
    return app.test_client()


@pytest.fixture
def sample_user(db):
    """Create a sample user for testing."""
    user = User(
        username='testuser',
        email='test@example.com',
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_post(db, sample_user):
    """Create a published sample post for testing."""
    post = Post(
        title='Sample Post',
        slug='sample-post',
        content='Sample content',
        author_id=sample_user.id,
        status='published',
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture
def auth_client(client, sample_user):
    """Provide a test client logged in as sample_user."""
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123',
    }, follow_redirects=True)
    return client
