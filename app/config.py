"""Application configuration classes for different environments."""

import os
from datetime import timedelta


class Config:
    """Base configuration shared across all environments."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_INACTIVITY_TIMEOUT = 1800  # 30 minutes in seconds


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URI', 'postgresql://localhost/rajblog_dev'
    )


class TestingConfig(Config):
    """Testing configuration with CSRF disabled and test database."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URI', 'postgresql://localhost/rajblog_test'
    )
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration with strict security requirements."""

    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True

    def __init__(self):
        super().__init__()
        if not os.environ.get('SECRET_KEY'):
            raise RuntimeError(
                'SECRET_KEY environment variable is not set. '
                'It is required in production mode.'
            )
        if not os.environ.get('DATABASE_URI'):
            raise RuntimeError(
                'DATABASE_URI environment variable is not set. '
                'It is required in production mode.'
            )

    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', '')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
