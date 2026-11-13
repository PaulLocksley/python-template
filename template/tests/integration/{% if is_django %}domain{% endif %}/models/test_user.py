import pytest
from django.contrib.auth import get_user_model

from tests.factories.user import UserFactory


@pytest.mark.django_db
def test_custom_user_is_the_auth_user_model() -> None:
    """Django resolves the swappable user model to the project's own."""
    user = UserFactory.create()

    assert isinstance(user, get_user_model())
    assert user.check_password("password")
