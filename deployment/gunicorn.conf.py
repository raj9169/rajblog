"""Gunicorn configuration file for production deployment."""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = 2 * multiprocessing.cpu_count() + 1

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Worker class
worker_class = "sync"

# Timeout
timeout = 120

# Graceful timeout
graceful_timeout = 30

# Keep alive
keepalive = 5

# Preload app for better memory usage with multiple workers
preload_app = True
