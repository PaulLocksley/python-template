"""Local development settings."""

from .base import *

DEBUG = True

INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar", "django_extensions"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
INTERNAL_IPS = ["127.0.0.1"]

# Assets are served by the Vite dev server (`just dev`) with hot reload.
DJANGO_VITE["default"]["dev_mode"] = True
