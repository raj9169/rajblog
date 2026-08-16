"""REST API endpoints for the personal blog."""

from flask import jsonify, request
from flask_login import current_user

from app.api import api_bp
from app.extensions import db
from app.models.comment import Comment
from app.models.post import Post
from app.utils import generate_slug


def post_to_dict(post: Post, include_content: bool = True) -> dict:
    """Serialize a Post to a dictionary for JSON response."""
    result = {
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'author': post.author.username,
        'status': post.status,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
    }
    if include_content:
        result['content'] = post.content
    else:
        result['content_excerpt'] = post.excerpt
    return result


def comment_to_dict(comment: Comment) -> dict:
    """Serialize a Comment to a dictionary for JSON response."""
    return {
        'id': comment.id,
        'content': comment.content,
        'author': comment.author.username,
        'post_id': comment.post_id,
        'created_at': comment.created_at.isoformat(),
        'updated_at': comment.updated_at.isoformat(),
    }


@api_bp.route('/posts', methods=['GET'])
def get_posts():
    """Return JSON array of published posts."""
    posts = Post.query.filter_by(status='published').order_by(
        Post.created_at.desc()
    ).all()
    return jsonify([post_to_dict(post, include_content=False) for post in posts])


@api_bp.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
    """Return full post JSON by ID."""
    post = Post.query.get(id)
    if post is None:
        return jsonify({'error': 'Resource not found'}), 404
    return jsonify(post_to_dict(post, include_content=True))


@api_bp.route('/posts', methods=['POST'])
def create_post():
    """Create a new post from JSON body. Requires authentication."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Request body must be valid JSON'}), 400

    title = data.get('title', '').strip() if data.get('title') else ''
    content = data.get('content', '').strip() if data.get('content') else ''

    if not title:
        return jsonify({'error': 'Title is required'}), 400
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    # Generate unique slug
    existing_slugs = [p.slug for p in Post.query.all()]
    slug = generate_slug(title, existing_slugs)

    post = Post(
        title=title,
        slug=slug,
        content=content,
        author_id=current_user.id,
        status='draft',
    )
    db.session.add(post)
    db.session.commit()

    return jsonify(post_to_dict(post, include_content=True)), 201


@api_bp.route('/posts/<int:id>', methods=['PUT'])
def update_post(id):
    """Update a post. Owner only."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401

    post = Post.query.get(id)
    if post is None:
        return jsonify({'error': 'Resource not found'}), 404

    if post.author_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Request body must be valid JSON'}), 400

    if 'title' in data:
        title = data['title'].strip() if data['title'] else ''
        if not title:
            return jsonify({'error': 'Title cannot be empty'}), 400
        post.title = title

    if 'content' in data:
        content = data['content'].strip() if data['content'] else ''
        if not content:
            return jsonify({'error': 'Content cannot be empty'}), 400
        post.content = content

    if 'status' in data:
        status = data['status']
        if status not in ('draft', 'published'):
            return jsonify({'error': 'Status must be "draft" or "published"'}), 400
        post.status = status

    db.session.commit()

    return jsonify(post_to_dict(post, include_content=True)), 200


@api_bp.route('/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    """Delete a post. Owner only."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401

    post = Post.query.get(id)
    if post is None:
        return jsonify({'error': 'Resource not found'}), 404

    if post.author_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403

    db.session.delete(post)
    db.session.commit()

    return '', 204


@api_bp.route('/posts/<int:id>/comments', methods=['POST'])
def create_comment(id):
    """Create a comment on a post. Requires authentication."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401

    post = Post.query.get(id)
    if post is None:
        return jsonify({'error': 'Resource not found'}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Request body must be valid JSON'}), 400

    content = data.get('content', '').strip() if data.get('content') else ''
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    if len(content) > Comment.MAX_CONTENT_LENGTH:
        return jsonify({
            'error': f'Comment must not exceed {Comment.MAX_CONTENT_LENGTH} characters'
        }), 400

    comment = Comment(
        content=content,
        author_id=current_user.id,
        post_id=post.id,
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment_to_dict(comment)), 201
