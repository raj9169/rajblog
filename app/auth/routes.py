"""Authentication routes for registration, login, and logout."""

import time

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm
from app.extensions import db
from app.models.user import User
from app.utils import sanitize_input


@auth_bp.before_app_request
def check_session_inactivity():
    """Check session inactivity timeout before each request."""
    if current_user.is_authenticated:
        from flask import current_app

        last_activity = session.get('last_activity')
        if last_activity is not None:
            timeout = current_app.config.get('SESSION_INACTIVITY_TIMEOUT', 1800)
            elapsed = time.time() - last_activity
            if elapsed > timeout:
                logout_user()
                session.clear()
                flash('Your session has expired due to inactivity.', 'info')
                return redirect(url_for('auth.login'))
        session['last_activity'] = time.time()


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Sanitize input
        try:
            username = sanitize_input(form.username.data)
        except ValueError:
            flash('Username contains invalid HTML content.', 'danger')
            return render_template('auth/register.html', form=form)

        # Check uniqueness of username
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username is already taken.', 'danger')
            return render_template('auth/register.html', form=form)

        # Check uniqueness of email
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email is already registered.', 'danger')
            return render_template('auth/register.html', form=form)

        # Create user with hashed password
        user = User(
            username=username,
            email=form.email.data,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html', form=form)

        # Log the user in with a permanent session (24hr lifetime)
        login_user(user)
        session.permanent = True
        session['last_activity'] = time.time()

        # Redirect to original URL if preserved in next parameter
        next_page = request.args.get('next')
        if next_page and _is_safe_url(next_page):
            return redirect(next_page)

        return redirect(url_for('blog.dashboard'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('blog.index'))


def _is_safe_url(target: str) -> bool:
    """Validate that the redirect target is a relative URL (no external redirects)."""
    # Only allow relative URLs (starting with /)
    # Reject protocol-relative URLs (starting with //) and absolute URLs
    if not target:
        return False
    if target.startswith('//') or '://' in target:
        return False
    if not target.startswith('/'):
        return False
    return True
