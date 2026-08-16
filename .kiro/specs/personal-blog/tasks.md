# Implementation Plan: Personal Blog

## Overview

Implementation of a personal blogging platform using Python Flask with PostgreSQL. The plan follows an incremental approach: project setup and configuration first, then data models, authentication, blog features, API layer, templates, and finally testing. Each task builds on the previous, ensuring no orphaned code.

## Tasks

- [x] 1. Set up project structure and configuration
  - [x] 1.1 Create directory structure and base files
    - Create the full directory structure as defined in the design: `app/`, `app/models/`, `app/auth/`, `app/blog/`, `app/api/`, `app/templates/`, `app/templates/auth/`, `app/templates/blog/`, `app/templates/errors/`, `app/static/css/`, `tests/`, `tests/properties/`, `deployment/`
    - Create `requirements.txt` with pinned dependencies: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, psycopg2-binary, gunicorn, python-dotenv, Werkzeug, pytest, hypothesis
    - Create `.env.example` documenting all required environment variables (SECRET_KEY, DATABASE_URI, FLASK_ENV)
    - Create `.gitignore` excluding .env, __pycache__, venv/, *.pyc, instance/, migrations/
    - _Requirements: 12.2, 12.3, 12.4_

  - [x] 1.2 Implement application configuration module
    - Create `app/config.py` with Config base class, DevelopmentConfig, TestingConfig, and ProductionConfig
    - Config must read SECRET_KEY and DATABASE_URI from environment variables
    - ProductionConfig must raise an error if SECRET_KEY or DATABASE_URI is missing
    - DevelopmentConfig enables debug, TestingConfig disables CSRF and uses test DB, ProductionConfig sets secure cookie flags
    - _Requirements: 12.1, 12.8, 8.4, 8.5_

  - [x] 1.3 Implement extensions module and application factory
    - Create `app/extensions.py` with instantiation of SQLAlchemy, Migrate, LoginManager, CSRFProtect
    - Create `app/__init__.py` with `create_app(config_name)` factory function
    - Factory must initialize extensions, register blueprints (auth, blog, api), register error handlers, configure logging in production
    - Exempt API blueprint from CSRF protection
    - Create `wsgi.py` entry point
    - _Requirements: 12.1, 8.1, 8.8, 9.1, 9.2, 9.3, 9.4_

- [x] 2. Implement data models and database migrations
  - [x] 2.1 Create User model
    - Create `app/models/__init__.py` and `app/models/user.py`
    - Implement User model with all columns: id, username (unique, 30 chars), email (unique, 254 chars), password_hash (256 chars), created_at, updated_at
    - Implement `set_password()` using Werkzeug's generate_password_hash and `check_password()` using check_password_hash
    - Implement UserMixin for Flask-Login integration
    - Add cascade delete relationships for posts and comments
    - Add user_loader callback for Flask-Login
    - _Requirements: 10.1, 10.5, 1.6, 10.7_

  - [x] 2.2 Create Post model
    - Create `app/models/post.py`
    - Implement Post model with all columns: id, title (200 chars), slug (250 chars, unique), content (text), author_id (FK to users), status (20 chars, default "draft"), created_at, updated_at
    - Add cascade delete relationship for comments
    - Add `excerpt` property returning first 200 characters of content
    - _Requirements: 10.2, 10.6, 10.7, 3.8_

  - [x] 2.3 Create Comment model
    - Create `app/models/comment.py`
    - Implement Comment model with all columns: id, content (text, 2000 chars), author_id (FK to users), post_id (FK to posts), created_at, updated_at
    - _Requirements: 10.3, 10.7_

  - [x] 2.4 Set up Flask-Migrate and generate initial migration
    - Configure Flask-Migrate in the application factory
    - Generate and apply the initial database migration script
    - _Requirements: 10.4_

- [x] 3. Implement utility functions
  - [x] 3.1 Implement slug generation and validation utilities
    - Create `app/utils.py` with `generate_slug(title, existing_slugs)` function
    - Slug algorithm: lowercase, replace whitespace with single hyphen, remove non-alphanumeric/hyphen chars, trim hyphens, append numeric suffix for duplicates
    - Implement `validate_email(email)` function: exactly one @, domain with at least one dot, ≤254 chars
    - Implement `validate_username(username)` function: 3-30 chars, [a-zA-Z0-9_-] only
    - Implement `sanitize_input(text)` function: strip whitespace, reject unescaped HTML tags
    - _Requirements: 3.3, 1.7, 1.8, 8.2_

  - [x] 3.2 Write property tests for slug generation
    - **Property 1: Slug generation produces valid URL-safe strings**
    - **Property 2: Slug uniqueness with suffix**
    - **Validates: Requirements 3.3**

  - [x] 3.3 Write property tests for validation utilities
    - **Property 3: Username validation correctness**
    - **Property 4: Email validation correctness**
    - **Validates: Requirements 1.7, 1.8**

- [x] 4. Checkpoint - Ensure models and utilities work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement authentication system
  - [x] 5.1 Create auth forms
    - Create `app/auth/forms.py` with RegistrationForm (username, email, password, confirm_password) and LoginForm (email, password)
    - RegistrationForm validates: username 3-30 chars [a-zA-Z0-9_-], email format, password 8-128 chars, password confirmation match
    - LoginForm validates: email and password required
    - Include CSRF token in all forms via Flask-WTF
    - _Requirements: 1.1, 1.4, 1.5, 1.7, 1.8, 2.6, 8.1_

  - [x] 5.2 Create auth blueprint and routes
    - Create `app/auth/__init__.py` registering the auth blueprint
    - Create `app/auth/routes.py` with register, login, and logout routes
    - Register route: validate form, check uniqueness of username and email, create User with hashed password, flash success, redirect to login
    - Login route: validate credentials, create session (24hr max, 30min inactivity timeout), redirect to dashboard or original URL (next parameter)
    - Logout route: terminate session, redirect to home
    - Protected route redirect: preserve original URL in `next` parameter
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 2.7_

  - [x] 5.3 Write property test for password hashing
    - **Property 5: Password hashing round-trip**
    - **Validates: Requirements 1.6, 2.1**

  - [x] 5.4 Write unit tests for authentication flows
    - Test successful registration, duplicate username, duplicate email, empty fields, invalid password length, invalid username format, invalid email format
    - Test successful login, invalid credentials, empty fields, session timeout
    - Test logout and redirect behavior
    - _Requirements: 1.1-1.8, 2.1-2.7, 13.1_

- [x] 6. Implement blog post management
  - [x] 6.1 Create blog forms
    - Create `app/blog/forms.py` with PostForm (title, content, status) and CommentForm (content)
    - PostForm validates: title 1-200 chars, content required, status in ["draft", "published"]
    - CommentForm validates: content 1-2000 chars after trim, non-whitespace-only
    - _Requirements: 3.1, 3.2, 3.5, 5.1, 5.2_

  - [x] 6.2 Create blog blueprint and post routes
    - Create `app/blog/__init__.py` registering the blog blueprint
    - Create `app/blog/routes.py` with index, post_detail, create_post, edit_post, delete_post routes
    - Index route: paginated published posts (10 per page), ordered by created_at desc, showing excerpt
    - Post detail: display full content, author, date, comments; return 404 for non-existent or draft posts (for non-authors)
    - Create post: validate form, generate unique slug, set author and draft status, redirect to detail
    - Edit post: verify ownership (403 if not owner), pre-populate form, update record including status and updated_at
    - Delete post: verify ownership, cascade delete comments, redirect to dashboard
    - _Requirements: 3.1-3.9, 4.1-4.5_

  - [x] 6.3 Implement comment route and dashboard/profile routes
    - Add comment route: validate content (1-2000 chars, non-whitespace), create comment, redirect to post detail; return 404 if post doesn't exist
    - Dashboard route: display user's posts with title, status, date, comment count, edit/delete links; show "no posts" message with create link if empty
    - Profile route: display username, email, account creation date
    - _Requirements: 5.1-5.6, 6.1-6.4_

  - [x] 6.4 Write property test for comment validation
    - **Property 7: Comment content validation and normalization**
    - **Validates: Requirements 5.1, 5.2**

  - [x] 6.5 Write unit tests for blog post management
    - Test post creation, editing, deletion, authorization checks, slug generation with duplicates
    - Test comment creation, validation errors, display ordering
    - Test dashboard with posts and empty state, profile display
    - _Requirements: 3.1-3.9, 5.1-5.6, 6.1-6.4, 13.2, 13.3_

- [x] 7. Checkpoint - Ensure blog functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement REST API layer
  - [x] 8.1 Create API blueprint and endpoints
    - Create `app/api/__init__.py` registering the api blueprint with /api prefix
    - Create `app/api/routes.py` with all REST endpoints
    - GET /api/posts: return JSON array of published posts (id, title, slug, content excerpt, author username, created_at)
    - GET /api/posts/<id>: return full post JSON (id, title, slug, content, author, status, created_at, updated_at)
    - POST /api/posts: authenticated, create post from JSON body (title, content), return 201
    - PUT /api/posts/<id>: owner-only, update fields (title, content, status), return 200
    - DELETE /api/posts/<id>: owner-only, delete post, return 204
    - POST /api/posts/<id>/comments: authenticated, create comment from JSON body (content), return 201
    - Implement JSON error responses: 400, 401, 403, 404
    - Implement `post_to_dict()` and `comment_to_dict()` serialization helpers
    - _Requirements: 7.1-7.11, 8.8_

  - [x] 8.2 Write property test for post serialization
    - **Property 6: Public visibility invariant**
    - **Property 8: Post serialization completeness**
    - **Validates: Requirements 4.4, 4.5, 7.1, 7.2**

  - [x] 8.3 Write unit tests for API endpoints
    - Test all CRUD operations with valid data
    - Test error responses: 400 (validation), 401 (unauthenticated), 403 (not owner), 404 (not found)
    - Test that only published posts appear in GET /api/posts
    - _Requirements: 7.1-7.11, 13.4, 13.5_

- [x] 9. Implement templates and frontend
  - [x] 9.1 Create base template and error pages
    - Create `app/templates/base.html` with Bootstrap 5 CDN, navigation bar (conditional links for auth state), flash message area, content block, footer
    - Create `app/templates/errors/404.html`, `app/templates/errors/403.html`, `app/templates/errors/500.html` extending base with descriptive messages and link to home
    - Create `app/static/css/style.css` for custom styles
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 9.1, 9.2, 9.3_

  - [x] 9.2 Create authentication templates
    - Create `app/templates/auth/login.html` with email/password form, CSRF token, error display, link to register
    - Create `app/templates/auth/register.html` with username/email/password/confirm form, CSRF token, error display, link to login
    - Forms must retain input on validation errors
    - _Requirements: 11.5, 8.1, 1.2, 1.3_

  - [x] 9.3 Create blog templates
    - Create `app/templates/index.html` with paginated post listing (title, author, date, excerpt, pagination controls)
    - Create `app/templates/blog/post_detail.html` with full content, author, date, comment list (ordered asc), comment form (hidden for unauthenticated with login prompt)
    - Create `app/templates/blog/create_post.html` and `app/templates/blog/edit_post.html` with title/content/status form and CSRF token
    - Create `app/templates/blog/dashboard.html` with post table (title, status, date, comment count, actions) and empty state
    - Create `app/templates/blog/profile.html` with user information display
    - _Requirements: 11.5, 4.1, 4.2, 5.3, 5.4, 6.1, 6.2, 6.3_

- [x] 10. Implement security measures
  - [x] 10.1 Configure security settings
    - Ensure CSRF protection is active on all HTML forms (via Flask-WTF integration)
    - Verify Jinja2 auto-escaping is enabled (Flask default)
    - Verify SQLAlchemy parameterized queries are used throughout (ORM usage)
    - Ensure API blueprint is exempted from CSRF
    - Add CSRF validation error handler returning 400
    - Implement input sanitization on all form submissions via `sanitize_input()`
    - _Requirements: 8.1, 8.2, 8.3, 8.6, 8.7, 8.8_

- [x] 11. Checkpoint - Ensure full application works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Create deployment and documentation files
  - [x] 12.1 Create deployment configuration files
    - Create `deployment/gunicorn.conf.py` with bind address (0.0.0.0:8000), worker count (2 * CPU + 1), access log configuration
    - Create `deployment/nginx.conf` with HTTPS termination, static file serving from /static, reverse proxy to Gunicorn
    - _Requirements: 12.5, 12.6_

  - [x] 12.2 Create README.md
    - Write README with project description, prerequisites, setup instructions, environment variable documentation, local development steps, running tests, and deployment instructions
    - _Requirements: 12.7_

- [x] 13. Implement test suite
  - [x] 13.1 Create test fixtures and configuration
    - Create `tests/conftest.py` with app fixture (testing config), client fixture, authenticated client fixture, sample_user and sample_post fixtures
    - Use database transaction rollback for test isolation
    - Configure separate test database
    - _Requirements: 13.6, 13.7_

  - [x] 13.2 Create comprehensive test modules
    - Create `tests/test_auth.py`: registration (success, duplicate username/email, empty fields, invalid format), login (success, invalid credentials, empty fields), logout, protected route redirect
    - Create `tests/test_blog.py`: create post (success, validation errors), edit post (owner, non-owner), delete post (owner, non-owner, cascade comments), dashboard display, profile display
    - Create `tests/test_comments.py`: create comment (success, empty, too long, whitespace-only), display ordering, unauthenticated access, non-existent post
    - Create `tests/test_api.py`: all CRUD operations, error responses (400, 401, 403, 404), visibility rules
    - Create `tests/test_errors.py`: custom 404, 403, 500 pages, no stack trace in production
    - _Requirements: 13.1-13.8_

- [x] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The application uses Python Flask with PostgreSQL as specified in the design
- All code uses SQLAlchemy ORM (parameterized queries by default) to prevent SQL injection
- Hypothesis library is used for property-based testing

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["2.1", "3.1"] },
    { "id": 4, "tasks": ["2.2", "2.3", "3.2", "3.3"] },
    { "id": 5, "tasks": ["2.4"] },
    { "id": 6, "tasks": ["5.1", "6.1"] },
    { "id": 7, "tasks": ["5.2", "5.3"] },
    { "id": 8, "tasks": ["5.4", "6.2"] },
    { "id": 9, "tasks": ["6.3", "6.4"] },
    { "id": 10, "tasks": ["6.5", "8.1"] },
    { "id": 11, "tasks": ["8.2", "8.3"] },
    { "id": 12, "tasks": ["9.1"] },
    { "id": 13, "tasks": ["9.2", "9.3"] },
    { "id": 14, "tasks": ["10.1"] },
    { "id": 15, "tasks": ["12.1", "12.2"] },
    { "id": 16, "tasks": ["13.1"] },
    { "id": 17, "tasks": ["13.2"] }
  ]
}
```
