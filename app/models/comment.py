"""Comment model for the personal blog."""

from datetime import datetime

from sqlalchemy.orm import validates

from app.extensions import db


class Comment(db.Model):
    """Blog comment model."""

    __tablename__ = 'comments'

    MAX_CONTENT_LENGTH = 2000

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @validates('content')
    def validate_content(self, key, value):
        """Validate comment content does not exceed maximum length."""
        if value and len(value) > self.MAX_CONTENT_LENGTH:
            raise ValueError(
                f'Comment content must not exceed {self.MAX_CONTENT_LENGTH} characters'
            )
        return value

    def __repr__(self) -> str:
        return f'<Comment {self.id}>'
