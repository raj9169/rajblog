# Requirements Document

## Introduction

A production-ready personal blogging platform built with Python Flask and PostgreSQL, designed as a portfolio project suitable for deployment on AWS. The application enables users to register, authenticate, create and manage blog posts, comment on posts, and view published content through a responsive web interface. The system provides both server-rendered HTML views and REST-style API endpoints, with comprehensive security, error handling, and deployment configurations.

## Glossary

- **Application**: The Flask-based personal blog web application
- **Visitor**: An unauthenticated user browsing the public blog
- **User**: A registered and authenticated individual interacting with the Application
- **Author**: A User who has created one or more Posts
- **Post**: A blog article containing a title, slug, content, status, and metadata
- **Comment**: A text response attached to a Post, authored by a User
- **Dashboard**: A protected page displaying a User's own Posts and management options
- **Slug**: A URL-friendly version of a Post title, used in routing
- **Session**: A server-side authentication state maintained via Flask-Login
- **CSRF_Token**: A unique token embedded in forms to prevent cross-site request forgery
- **Password_Hash**: A one-way cryptographic hash of a User's password stored in the database
- **API**: The REST-style JSON endpoint layer of the Application
- **Database**: The PostgreSQL relational database storing all persistent data

## Requirements

### Requirement 1: User Registration

**User Story:** As a Visitor, I want to register an account with a username, email, and password, so that I can create Posts and Comments on the blog.

#### Acceptance Criteria

1. WHEN a Visitor submits a registration form with a valid username, email, and password, THE Application SHALL create a new User record in the Database with a Password_Hash and redirect to the login page.
2. WHEN a Visitor submits a registration form with a username that already exists in the Database, THE Application SHALL display an error message indicating the username is taken and retain the form input.
3. WHEN a Visitor submits a registration form with an email that already exists in the Database, THE Application SHALL display an error message indicating the email is already registered and retain the form input.
4. IF a Visitor submits a registration form with an empty username, empty email, or empty password, THEN THE Application SHALL display a validation error for each missing field without creating a User record.
5. IF a Visitor submits a registration form with a password shorter than 8 characters or longer than 128 characters, THEN THE Application SHALL display a validation error indicating the allowed password length range and retain the form input.
6. THE Application SHALL store passwords exclusively as Password_Hash values using Werkzeug's generate_password_hash function.
7. IF a Visitor submits a registration form with a username shorter than 3 characters, longer than 30 characters, or containing characters other than letters, digits, underscores, or hyphens, THEN THE Application SHALL display a validation error indicating the username requirements and retain the form input.
8. IF a Visitor submits a registration form with an email that does not contain exactly one @ symbol followed by a domain with at least one dot, or exceeds 254 characters in total length, THEN THE Application SHALL display a validation error indicating a valid email is required and retain the form input.

### Requirement 2: User Authentication

**User Story:** As a registered User, I want to log in and log out securely, so that I can access protected features and manage my content.

#### Acceptance Criteria

1. WHEN a User submits a login form with a valid email and correct password, THE Application SHALL create a Session with a maximum lifetime of 24 hours and a 30-minute inactivity timeout, and redirect the User to the Dashboard.
2. WHEN a User submits a login form with an invalid email or incorrect password, THE Application SHALL display a generic error message stating credentials are invalid without revealing which field is incorrect.
3. WHEN an authenticated User requests the logout endpoint, THE Application SHALL terminate the Session and redirect to the home page.
4. WHILE a User is not authenticated, THE Application SHALL redirect requests to protected routes to the login page and preserve the originally requested URL so the User can be redirected back after successful login.
5. WHILE a User is authenticated, THE Application SHALL make the current User identity available to all templates and route handlers via Flask-Login.
6. IF a User submits a login form with an empty email or empty password field, THEN THE Application SHALL display a validation error indicating all fields are required without attempting authentication.
7. IF a User's Session expires due to inactivity timeout or maximum lifetime, THEN THE Application SHALL terminate the Session and redirect the next request to the login page.

### Requirement 3: Blog Post Management

**User Story:** As an Author, I want to create, edit, publish, and delete my blog posts, so that I can share content and maintain my blog.

#### Acceptance Criteria

1. WHEN an authenticated User submits a create post form with a title between 1 and 200 characters and non-empty content, THE Application SHALL create a new Post record with an auto-generated Slug, set the author_id to the current User, set the status to "draft", and redirect to the Post detail page.
2. IF an authenticated User submits a create post form with an empty title, a title exceeding 200 characters, or empty content, THEN THE Application SHALL display validation errors for each invalid field without creating a Post record.
3. THE Application SHALL generate a Slug for each Post by converting the title to lowercase, replacing spaces and consecutive whitespace with a single hyphen, removing all characters that are not lowercase letters, digits, or hyphens, and trimming leading or trailing hyphens. IF a generated Slug already exists in the Database, THEN THE Application SHALL append a numeric suffix (e.g., "-1", "-2") to produce a unique Slug.
4. WHEN an Author requests the edit page for a Post they own, THE Application SHALL display the edit form pre-populated with the current Post title, content, and status.
5. WHEN an Author submits an updated Post with a valid title (1 to 200 characters), non-empty content, and a valid status ("draft" or "published"), THE Application SHALL update the Post record including the status field, set the updated_at timestamp, and redirect to the Post detail page.
6. WHEN an Author requests deletion of a Post they own, THE Application SHALL remove the Post and all associated Comments from the Database and redirect to the Dashboard.
7. IF a User requests to edit or delete a Post they do not own, THEN THE Application SHALL return a 403 Forbidden response.
8. THE Application SHALL support Post status values of "draft" and "published" only, with "draft" as the default status for new Posts.
9. WHEN an Author submits the edit form for a Post they own with the status changed from "draft" to "published", THE Application SHALL update the Post status to "published" and set the updated_at timestamp.

### Requirement 4: Blog Post Display

**User Story:** As a Visitor, I want to browse and read published blog posts, so that I can consume the blog content.

#### Acceptance Criteria

1. WHEN a Visitor requests the home page, THE Application SHALL display a paginated list of published Posts (10 posts per page) ordered by created_at descending, showing the title, Author username, creation date, and a content excerpt of up to 200 characters.
2. WHEN a Visitor requests a Post detail page using its Slug, THE Application SHALL display the full Post content, Author username, creation date, and all associated Comments.
3. IF a Visitor requests a Post detail page with a Slug that does not exist in the Database, THEN THE Application SHALL return a 404 Not Found response with a custom error page.
4. WHILE a Post has a status of "draft", THE Application SHALL exclude the Post from the public listing.
5. IF a non-Author User or Visitor requests the detail page of a Post with status "draft", THEN THE Application SHALL return a 404 Not Found response without revealing the existence of the draft Post.

### Requirement 5: Comment System

**User Story:** As a User, I want to comment on blog posts, so that I can engage in discussion with Authors and other readers.

#### Acceptance Criteria

1. WHEN an authenticated User submits a comment form on a Post detail page with content containing at least 1 non-whitespace character and not exceeding 2000 characters, THE Application SHALL create a Comment record associated with the Post and the current User with leading and trailing whitespace trimmed from the content, then redirect back to the Post detail page.
2. IF an authenticated User submits a comment form with empty content, whitespace-only content, or content exceeding 2000 characters, THEN THE Application SHALL display a validation error indicating the content requirement that was not met and retain the submitted form input.
3. WHILE a User is not authenticated, THE Application SHALL hide the comment form and display a prompt to log in to comment.
4. WHEN a Post detail page is loaded, THE Application SHALL display all Comments for that Post ordered by created_at ascending, showing the Comment content, Author username, and creation date.
5. WHEN an Author views their Dashboard, THE Application SHALL display the total Comment count for each of the Author's Posts.
6. IF an authenticated User submits a comment form referencing a Post that does not exist in the Database, THEN THE Application SHALL return a 404 Not Found response.

### Requirement 6: User Profile and Dashboard

**User Story:** As a User, I want to view and manage my profile and content from a central dashboard, so that I can track and organize my blog activity.

#### Acceptance Criteria

1. WHEN an authenticated User requests the Dashboard, THE Application SHALL display all Posts owned by the User ordered by created_at descending, with title, status, creation date, Comment count, and action links for edit and delete.
2. WHEN an authenticated User requests the Dashboard and they have no Posts, THE Application SHALL display a message indicating no posts exist and a link to create a new Post.
3. WHEN an authenticated User requests the profile page, THE Application SHALL display the User's username, email, and account creation date.
4. WHILE a User is not authenticated, THE Application SHALL redirect Dashboard and profile requests to the login page.

### Requirement 7: REST API Endpoints

**User Story:** As a developer, I want REST-style API endpoints for Posts and Comments, so that the blog can support programmatic access and future frontend integrations.

#### Acceptance Criteria

1. WHEN a GET request is made to /api/posts, THE API SHALL return a JSON array of all published Posts with id, title, slug, content excerpt (first 200 characters of content), author username, and created_at fields.
2. WHEN a GET request is made to /api/posts/<id>, THE API SHALL return a JSON object with the full Post details including id, title, slug, content, author username, status, created_at, and updated_at.
3. WHEN an authenticated User sends a POST request to /api/posts with a JSON body containing a non-empty title and non-empty content, THE API SHALL create a new Post and return the created Post as JSON with a 201 status code.
4. WHEN an authenticated Author sends a PUT request to /api/posts/<id> with a JSON body containing one or more updatable fields (title, content, status), THE API SHALL update the Post and return the updated Post as JSON with a 200 status code.
5. WHEN an authenticated Author sends a DELETE request to /api/posts/<id> for a Post they own, THE API SHALL delete the Post and return a 204 No Content response.
6. WHEN an authenticated User sends a POST request to /api/posts/<id>/comments with a JSON body containing non-empty content, THE API SHALL create a Comment and return it as JSON with a 201 status code.
7. IF an unauthenticated request is made to a protected API endpoint, THEN THE API SHALL return a 401 Unauthorized JSON response with an error message indicating authentication is required.
8. IF a User sends a PUT or DELETE request to /api/posts/<id> for a Post they do not own, THEN THE API SHALL return a 403 Forbidden JSON response.
9. IF a request is made to /api/posts/<id> or /api/posts/<id>/comments and the specified Post id does not exist in the Database, THEN THE API SHALL return a 404 Not Found JSON response with an error message indicating the resource was not found.
10. IF a POST or PUT request is made to an API endpoint with a missing or malformed JSON body, or with required fields empty, THEN THE API SHALL return a 400 Bad Request JSON response with an error message indicating the validation failure.
11. IF an authenticated User sends a POST request to /api/posts/<id>/comments and the specified Post id does not exist, THEN THE API SHALL return a 404 Not Found JSON response.

### Requirement 8: Security

**User Story:** As a system operator, I want the Application to implement security best practices, so that user data is protected and the system is resistant to common attacks.

#### Acceptance Criteria

1. THE Application SHALL include a CSRF_Token in every HTML form and validate the token on form submission.
2. THE Application SHALL validate all user input on the server side by stripping leading and trailing whitespace, enforcing maximum field lengths per Database schema, and rejecting input containing unescaped HTML tags before processing or storing data.
3. THE Application SHALL use parameterized queries via SQLAlchemy ORM to prevent SQL injection attacks.
4. THE Application SHALL store sensitive configuration values (database URI, secret key) in environment variables, not in source code.
5. WHILE the Application is running in production mode, THE Application SHALL set the Flask session cookie with httponly and secure flags.
6. IF a form submission contains an invalid or missing CSRF_Token, THEN THE Application SHALL reject the request and return a 400 Bad Request response.
7. THE Application SHALL enable Jinja2 auto-escaping for all template rendering to prevent cross-site scripting (XSS) attacks.
8. THE Application SHALL exempt API endpoints (routes prefixed with /api/) from CSRF token validation to allow programmatic access.

### Requirement 9: Error Handling

**User Story:** As a Visitor or User, I want clear and helpful error pages, so that I understand when something goes wrong without seeing sensitive system information.

#### Acceptance Criteria

1. WHEN a request is made to a URL that does not match any route, THE Application SHALL return a custom 404 Not Found page using the base template layout with a link to the home page.
2. WHEN a User attempts to access a resource they are not authorized to view, THE Application SHALL return a custom 403 Forbidden page using the base template layout with a link to the home page.
3. IF an unhandled exception occurs during request processing, THEN THE Application SHALL return a custom 500 Internal Server Error page using the base template layout without exposing stack traces, configuration values, or internal paths.
4. WHILE the Application is running in production mode, THE Application SHALL log exceptions with full stack traces to the server log and display only the custom error page to the User.

### Requirement 10: Database and Data Model

**User Story:** As a developer, I want a well-structured database schema with migrations, so that the data layer is maintainable and the schema can evolve safely.

#### Acceptance Criteria

1. THE Database SHALL store User records with id (integer, primary key, auto-increment), username (string, max 30 characters, unique, not null), email (string, max 254 characters, unique, not null), password_hash (string, max 256 characters, not null), created_at (datetime, not null), and updated_at (datetime, not null) columns.
2. THE Database SHALL store Post records with id (integer, primary key, auto-increment), title (string, max 200 characters, not null), slug (string, max 250 characters, unique, not null), content (text, not null), author_id (integer, foreign key to User, not null), status (string, max 20 characters, not null, default "draft"), created_at (datetime, not null), and updated_at (datetime, not null) columns.
3. THE Database SHALL store Comment records with id (integer, primary key, auto-increment), content (text, max 2000 characters, not null), author_id (integer, foreign key to User, not null), post_id (integer, foreign key to Post, not null), created_at (datetime, not null), and updated_at (datetime, not null) columns.
4. THE Application SHALL use Flask-Migrate with Alembic to manage database schema changes through versioned migration scripts.
5. WHEN a User record is deleted, THE Database SHALL cascade-delete all associated Post and Comment records.
6. WHEN a Post record is deleted, THE Database SHALL cascade-delete all associated Comment records.
7. THE Application SHALL automatically set created_at to the current UTC timestamp when a record is first inserted, and automatically set updated_at to the current UTC timestamp on every insert and update.

### Requirement 11: Frontend and Templates

**User Story:** As a Visitor or User, I want a professional, responsive web interface, so that the blog is usable and visually appealing across devices.

#### Acceptance Criteria

1. THE Application SHALL use Jinja2 template inheritance with a base.html layout that includes a navigation bar, flash message area, content block, and footer.
2. THE Application SHALL use Bootstrap 5 CSS framework loaded via CDN to provide responsive layout and component styling across viewport widths from 320px to 1920px.
3. WHEN a User performs an action that succeeds or fails (login, registration, post creation, deletion), THE Application SHALL display a flash message indicating the result using a dismissible Bootstrap alert component.
4. THE Application SHALL provide navigation links to Home, Login, Register for unauthenticated Visitors, and Home, Dashboard, New Post, Logout for authenticated Users.
5. THE Application SHALL include the following templates using base.html inheritance: index.html, login.html, register.html, dashboard.html, post_detail.html, create_post.html, edit_post.html, profile.html, 404.html, and 500.html.

### Requirement 12: Application Configuration and Deployment

**User Story:** As a developer, I want the application to be configured for both local development and AWS production deployment, so that I can develop efficiently and deploy reliably.

#### Acceptance Criteria

1. THE Application SHALL load configuration from environment variables using a configuration class selected by the FLASK_ENV environment variable, with distinct classes for development (debug enabled, local database URI), testing (testing flag enabled, separate test database URI), and production (debug disabled, secure secret key required).
2. THE Application SHALL include a requirements.txt file listing all Python dependencies with pinned versions.
3. THE Application SHALL include a .env.example file documenting all required environment variables without actual secret values.
4. THE Application SHALL include a .gitignore file excluding .env, __pycache__, virtual environment directories, and database files.
5. THE Application SHALL include a Gunicorn configuration file specifying a bind address, worker count, and access log configuration for production deployment behind Nginx.
6. THE Application SHALL include an Nginx configuration file with HTTPS termination, static file serving, and reverse proxy to Gunicorn.
7. THE Application SHALL include a README.md with setup instructions, environment variable documentation, local development steps, and deployment instructions.
8. IF a required environment variable (SECRET_KEY or DATABASE_URI) is not set when the Application starts in production mode, THEN THE Application SHALL raise an error at startup indicating which variable is missing.

### Requirement 13: Testing

**User Story:** As a developer, I want comprehensive automated tests, so that I can verify application correctness and prevent regressions.

#### Acceptance Criteria

1. THE Application SHALL include pytest-based test suites covering user registration, login, and logout flows including both successful paths and validation error paths as defined in Requirements 1 and 2.
2. THE Application SHALL include pytest-based test suites covering Post creation, editing, deletion, and authorization checks including both successful paths and error paths as defined in Requirement 3.
3. THE Application SHALL include pytest-based test suites covering Comment creation and validation including both successful paths and error paths as defined in Requirement 5.
4. THE Application SHALL include pytest-based tests verifying that unauthorized users cannot access protected routes and receive appropriate redirects or error responses.
5. THE Application SHALL include pytest-based tests verifying correct 404 responses for non-existent resources.
6. THE Application SHALL use a separate test database configuration to avoid affecting development or production data.
7. WHEN tests are executed, THE Application SHALL provide test fixtures that create and tear down test data in isolation using database transaction rollback.
8. THE Application SHALL pass all tests when executed via a single `pytest` command from the project root directory.
