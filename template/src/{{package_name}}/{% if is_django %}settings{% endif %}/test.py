"""Test settings."""

from .base import *

# Emit Vite dev-server tags so templates render without a frontend build.
DJANGO_VITE["default"]["dev_mode"] = True

# Run tasks inline, at enqueue time.
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
    },
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
