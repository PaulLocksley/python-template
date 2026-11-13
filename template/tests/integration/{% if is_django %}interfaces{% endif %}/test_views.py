from django.test import Client
from django.urls import reverse


def test_home_renders_the_full_page(client: Client) -> None:
    """A normal request gets the whole document."""
    response = client.get(reverse("home"), {"name": "Ada"})

    assert response.status_code == 200
    assert b"<html" in response.content
    assert b"Hello, Ada!" in response.content


def test_home_renders_only_the_partial_for_htmx(client: Client) -> None:
    """An htmx request gets just the greeting fragment."""
    response = client.get(reverse("home"), {"name": "Ada"}, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert b"<html" not in response.content
    assert b"Hello, Ada!" in response.content


def test_home_rejects_post(client: Client) -> None:
    """The home view is read-only."""
    assert client.post(reverse("home")).status_code == 405
