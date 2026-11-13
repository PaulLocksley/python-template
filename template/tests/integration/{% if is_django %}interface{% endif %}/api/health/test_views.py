import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_health_check_reports_ok(client: Client) -> None:
    """The health endpoint answers once the database is reachable."""
    response = client.get(reverse("healthz"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
