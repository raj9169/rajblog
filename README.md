# RajBlog — Personal Blogging Platform

A production-ready personal blogging platform built with Python Flask and PostgreSQL. Features user registration and authentication, blog post management with drafts and publishing, a comment system, and a REST API for programmatic access.

## Prerequisites

- Python 3.10+
- PostgreSQL 13+
- pip (Python package manager)

## Project Structure

```
rajblog/
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── config.py            # Configuration classes (dev, test, prod)
│   ├── extensions.py        # Flask extension initialization
│   ├── utils.py             # Utility functions (slug generation, validation)
│   ├── models/              # SQLAlchemy models (User, Post, Comment)
│   ├── auth/                # Authentication blueprint (login, register, logout)
│   ├── blog/                # Blog blueprint (posts, comments, dashboard)
│   ├── api/                 # REST API blueprint
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # Static assets (CSS)
├── migrations/              # Alembic database migration scripts
├── tests/                   # pytest test suites
│   ├── conftest.py          # Test fixtures and configuration
│   ├── test_auth_routes.py  # Authentication route tests
│   ├── test_blog.py         # Blog post tests
│   ├── test_comments.py     # Comment system tests
│   ├── test_api.py          # REST API tests
│   └── properties/          # Property-based tests (Hypothesis)
├── deployment/              # Production deployment configs
│   ├── gunicorn.conf.py     # Gunicorn WSGI server configuration
│   └── nginx.conf           # Nginx reverse proxy configuration
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies (pinned versions)
├── wsgi.py                  # WSGI entry point
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd rajblog
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values (see [Environment Variables](#environment-variables) below).

### 5. Create the database

```bash
# Connect to PostgreSQL and create the database
createdb rajblog_dev
```

### 6. Run database migrations

```bash
flask db upgrade
```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | Yes | Secret key for session management and CSRF protection. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` | `a1b2c3d4...` |
| `DATABASE_URI` | Yes | PostgreSQL connection URI | `postgresql://user:pass@localhost/rajblog_dev` |
| `FLASK_ENV` | No | Application environment. One of `development`, `testing`, or `production`. Defaults to `development`. | `development` |

In production, both `SECRET_KEY` and `DATABASE_URI` are required. The application will raise an error at startup if either is missing.

## Local Development

Start the development server:

```bash
# Using Flask's built-in server (with debug mode)
flask run

# Or using the WSGI entry point
python wsgi.py
```

The application will be available at `http://localhost:5000`.

## Running Tests

Tests use SQLite in-memory databases by default, so no PostgreSQL setup is required for testing.

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only property-based tests
pytest tests/properties/

# Run with coverage report
pytest --cov=app --cov-report=html
```

## Deployment

The application is designed for deployment on AWS EC2 behind Nginx with Gunicorn as the WSGI server.

### 1. Install production dependencies

```bash
pip install -r requirements.txt
```

### 2. Set production environment variables

Ensure `FLASK_ENV=production`, `SECRET_KEY`, and `DATABASE_URI` are set in your environment or via a `.env` file.

### 3. Run database migrations

```bash
flask db upgrade
```

### 4. Start with Gunicorn

```bash
gunicorn -c deployment/gunicorn.conf.py wsgi:app
```

### 5. Configure Nginx

Use the provided `deployment/nginx.conf` as a template for your Nginx configuration. It includes:

- HTTPS termination with SSL certificates
- Static file serving
- Reverse proxy to Gunicorn

```bash
# Copy and adapt the nginx config
sudo cp deployment/nginx.conf /etc/nginx/sites-available/rajblog
sudo ln -s /etc/nginx/sites-available/rajblog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## API Endpoints

The application exposes a REST API under the `/api/` prefix:

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/posts` | Public | List all published posts |
| GET | `/api/posts/<id>` | Public | Get a single post |
| POST | `/api/posts` | Required | Create a new post |
| PUT | `/api/posts/<id>` | Owner | Update a post |
| DELETE | `/api/posts/<id>` | Owner | Delete a post |
| POST | `/api/posts/<id>/comments` | Required | Add a comment to a post |

API errors return JSON responses in the format: `{"error": "message"}`.

## License

This project is a personal portfolio project.
