"""Blog forms for post creation/editing and commenting."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError


class PostForm(FlaskForm):
    """Form for creating and editing blog posts."""

    title = StringField(
        'Title',
        validators=[
            DataRequired(message='Title is required.'),
            Length(
                min=1,
                max=200,
                message='Title must be between 1 and 200 characters.',
            ),
        ],
    )
    content = TextAreaField(
        'Content',
        validators=[
            DataRequired(message='Content is required.'),
        ],
    )
    status = SelectField(
        'Status',
        choices=[('draft', 'Draft'), ('published', 'Published')],
        validators=[
            DataRequired(message='Status is required.'),
        ],
    )

    def validate_status(self, field):
        """Validate that status is one of the allowed values."""
        if field.data not in ('draft', 'published'):
            raise ValidationError('Status must be "draft" or "published".')


class CommentForm(FlaskForm):
    """Form for adding comments to blog posts."""

    content = TextAreaField(
        'Comment',
        validators=[
            DataRequired(message='Comment content is required.'),
        ],
    )

    def validate_content(self, field):
        """Validate content is non-whitespace-only and 1-2000 chars after trim."""
        if not field.data:
            return

        trimmed = field.data.strip()

        if len(trimmed) == 0:
            raise ValidationError(
                'Content must contain at least one non-whitespace character.'
            )

        if len(trimmed) > 2000:
            raise ValidationError(
                'Comment must not exceed 2000 characters.'
            )
