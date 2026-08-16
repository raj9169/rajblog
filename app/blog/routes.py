"""Blog routes for post CRUD, dashboard, and profile."""

from datetime import datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blog import blog_bp
from app.blog.forms import CommentForm, PostForm
from app.extensions import db
from app.models.comment import Comment
from app.models.post import Post
from app.utils import generate_slug, sanitize_input


@blog_bp.route('/')
def index():
    """Display paginated list of published posts."""
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(status='published').order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=10)
    return render_template('index.html', pagination=pagination, posts=pagination.items)


@blog_bp.route('/post/<slug>')
def post_detail(slug):
    """Display a single post with full content and comments."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    # Draft posts are only visible to their author
    if post.status == 'draft':
        if not current_user.is_authenticated or current_user.id != post.author_id:
            abort(404)

    comments = post.comments.order_by(db.text('created_at asc')).all()
    return render_template('blog/post_detail.html', post=post, comments=comments)


@blog_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new blog post."""
    form = PostForm()

    if form.validate_on_submit():
        # Sanitize inputs
        try:
            title = sanitize_input(form.title.data)
            content = sanitize_input(form.content.data)
        except ValueError:
            flash('Input contains invalid HTML content.', 'danger')
            return render_template('blog/create_post.html', form=form)

        # Get existing slugs for uniqueness check
        existing_slugs = [
            row[0] for row in Post.query.with_entities(Post.slug).all()
        ]
        slug = generate_slug(title, existing_slugs)

        post = Post(
            title=title,
            slug=slug,
            content=content,
            author_id=current_user.id,
            status=form.status.data,
        )
        db.session.add(post)
        db.session.commit()

        flash('Post created successfully.', 'success')
        return redirect(url_for('blog.post_detail', slug=post.slug))

    return render_template('blog/create_post.html', form=form)


@blog_bp.route('/post/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    """Edit an existing blog post."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    # Ownership check
    if post.author_id != current_user.id:
        abort(403)

    form = PostForm(obj=post)

    if form.validate_on_submit():
        # Sanitize inputs
        try:
            title = sanitize_input(form.title.data)
            content = sanitize_input(form.content.data)
        except ValueError:
            flash('Input contains invalid HTML content.', 'danger')
            return render_template('blog/edit_post.html', form=form, post=post)

        post.title = title
        post.content = content
        post.status = form.status.data
        post.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Post updated successfully.', 'success')
        return redirect(url_for('blog.post_detail', slug=post.slug))

    return render_template('blog/edit_post.html', form=form, post=post)


@blog_bp.route('/post/<slug>/delete', methods=['POST'])
@login_required
def delete_post(slug):
    """Delete a blog post and its associated comments."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    # Ownership check
    if post.author_id != current_user.id:
        abort(403)

    db.session.delete(post)
    db.session.commit()

    flash('Post deleted successfully.', 'success')
    return redirect(url_for('blog.dashboard'))


@blog_bp.route('/post/<slug>/comment', methods=['POST'])
@login_required
def add_comment(slug):
    """Add a comment to a blog post."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    form = CommentForm()
    if form.validate_on_submit():
        # Sanitize input
        try:
            trimmed_content = sanitize_input(form.content.data)
        except ValueError:
            flash('Comment contains invalid HTML content.', 'danger')
            return redirect(url_for('blog.post_detail', slug=slug))

        comment = Comment(
            content=trimmed_content,
            author_id=current_user.id,
            post_id=post.id,
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'error')

    return redirect(url_for('blog.post_detail', slug=slug))


@blog_bp.route('/dashboard')
@login_required
def dashboard():
    """Display user's post dashboard."""
    posts = Post.query.filter_by(author_id=current_user.id).order_by(
        Post.created_at.desc()
    ).all()
    return render_template('blog/dashboard.html', posts=posts)


@blog_bp.route('/profile')
@login_required
def profile():
    """Display user profile."""
    return render_template('blog/profile.html', user=current_user)
