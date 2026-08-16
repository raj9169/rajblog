"""Authentication forms for registration and login."""

import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError,
)


class RegistrationForm(FlaskForm):
    """User registration form with validation."""

    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(
                min=3,
                max=30,
                message='Username must be between 3 and 30 characters.',
            ),
        ],
    )
    email = EmailField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.'),
            Length(max=254, message='Email must not exceed 254 characters.'),
        ],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(
                min=8,
                max=128,
                message='Password must be between 8 and 128 characters.',
            ),
        ],
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.'),
        ],
    )

    def validate_username(self, field):
        """Validate username contains only allowed characters."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', field.data):
            raise ValidationError(
                'Username may only contain letters, digits, underscores, or hyphens.'
            )


class LoginForm(FlaskForm):
    """User login form."""

    email = EmailField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
        ],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
        ],
    )
