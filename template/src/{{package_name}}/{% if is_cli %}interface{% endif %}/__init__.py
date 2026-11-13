"""Interface: entry points into the system (the command line).

Highest layer. Keep it thin: parse input, call a use case (or domain rule),
present the result. May not import vendors.
"""
