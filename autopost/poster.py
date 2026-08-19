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


def get_or_create_bot_user(app):
    """Get or create the bot user for auto-posting."""
    with app.app_context():
        bot = User.query.filter_by(username="rajblog-bot").first()
        if not bot:
            bot = User(
                username="rajblog-bot",
                email="bot@stayhealthylife.in",
            )
            bot.set_password(os.environ.get("BOT_PASSWORD", "auto-post-secure-2024!"))
            db.session.add(bot)
            db.session.commit()
            print("Created bot user: rajblog-bot")
        return bot


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
        # Get or create bot user
        bot = User.query.filter_by(username="rajblog-bot").first()
        if not bot:
            bot = User(
                username="rajblog-bot",
                email="bot@stayhealthylife.in",
            )
            bot.set_password(os.environ.get("BOT_PASSWORD", "auto-post-secure-2024!"))
            db.session.add(bot)
            db.session.commit()
            print("Created bot user: rajblog-bot")

        bot_id = bot.id
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
            author_id=bot_id,
            status="published",
        )
        db.session.add(post)
        db.session.commit()

        print(f"PUBLISHED: {title} (/{slug})")
        return True
