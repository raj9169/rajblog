"""Post model for the personal blog."""

from datetime import datetime

from app.extensions import db


class Post(db.Model):
    """Blog post model."""

    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    comments = db.relationship(
        'Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan'
    )

    @property
    def excerpt(self) -> str:
        """Return first 200 characters of content."""
        return self.content[:200] if self.content else ''

    def __repr__(self) -> str:
        return f'<Post {self.title}>'
