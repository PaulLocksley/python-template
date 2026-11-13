"""Request types for views."""

from typing import TYPE_CHECKING

from django.http import HttpRequest

if TYPE_CHECKING:
    from django_htmx.middleware import HtmxDetails


class HtmxHttpRequest(HttpRequest):
    """A request as seen after ``HtmxMiddleware``, for annotating views."""

    htmx: HtmxDetails
