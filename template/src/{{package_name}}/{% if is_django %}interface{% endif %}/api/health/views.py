"""Health check endpoint."""

from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def healthz(request: HttpRequest) -> JsonResponse:  # noqa: ARG001
    """Report liveness, including database connectivity."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})
