"""The project's user model."""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user, in place from the first migration so it can evolve freely."""
