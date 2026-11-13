"""Interface: entry points into the system, split into ``api`` and ``ui``.

Highest layer. Keep it thin: parse input, call a use case (or domain rule),
present the result. May not import vendors.
"""
