"""Post generated content to the RajBlog Flask app."""

import os
import sys

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.post import Post
from app.models.user import User
from app.utils import generate_slug


def is_duplicate(title: str, slug: str) -> bool:
    """Check if a post with similar title or slug already exists."""
    # Check exact slug match
    if Post.query.filter_by(slug=slug).first():
        return True

    # Check similar titles (case-insensitive)
    existing = Post.query.filter(
        Post.title.ilike(f"%{title[:40]}%")
    ).first()
    if existing:
        return True

    return False


def publish_post(post_data: dict) -> bool:
    """Publish a generated post to the database."""
    app = create_app()

    with app.app_context():
        # Find the author by email from env config
        author_email = os.environ.get("AUTOPOST_AUTHOR_EMAIL", "")
        
        if author_email:
            author = User.query.filter_by(email=author_email).first()
            if not author:
                print(f"ERROR: No user found with email '{author_email}'. Register first.")
                return False
        else:
            # Fallback: use first user in database
            author = User.query.first()
            if not author:
                print("ERROR: No users in database. Register an account first.")
                return False

        author_id = author.id
        title = post_data["title"]
        slug = post_data["slug"]

        # Check for duplicates
        if is_duplicate(title, slug):
            print(f"SKIP (duplicate): {title}")
            return False

        # Ensure slug is unique
        existing_slugs = [row[0] for row in Post.query.with_entities(Post.slug).all()]
        if slug in existing_slugs:
            slug = generate_slug(title, existing_slugs)

        # Create and publish the post
        post = Post(
            title=title,
            slug=slug,
            content=post_data["content"],
            author_id=author_id,
            status="published",
        )
        db.session.add(post)
        db.session.commit()

        print(f"PUBLISHED: {title} (/{slug}) — by {author.username}")
        return True
