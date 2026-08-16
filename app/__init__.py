"""Application factory for the personal blog."""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, render_template, request
from flask_wtf.csrf import CSRFError

from app.config import config
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name: str = None) -> Flask:
    """
    Creates and configures the Flask application instance.

    Args:
        config_name: One of 'development', 'testing', 'production'.
                     Defaults to FLASK_ENV environment variable.

    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import models so they are registered with SQLAlchemy metadata
    from app import models  # noqa: F401

    # Register blueprints
    from app.auth import auth_bp
    from app.blog import blog_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(api_bp)

    # Exempt API blueprint from CSRF protection
    csrf.exempt(api_bp)

    # Register user loader placeholder (overridden when User model is available)
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from app.models.user import User
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Register error handlers
    _register_error_handlers(app)

    # Configure logging in production
    if not app.debug and not app.testing:
        _configure_logging(app)

    return app


def _register_error_handlers(app: Flask) -> None:
    """Register custom error handlers for the application."""

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/403.html'), 400

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500


def _configure_logging(app: Flask) -> None:
    """Configure file-based logging for production."""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler(
        'logs/rajblog.log', maxBytes=10240000, backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('RajBlog startup')
