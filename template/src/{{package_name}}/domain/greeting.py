"""Example domain object. Replace with your own domain."""

from dataclasses import dataclass

DEFAULT_NAME = "world"


@dataclass(frozen=True, slots=True)
class Greeting:
    """A greeting addressed to someone."""

    name: str

    def message(self) -> str:
        """Return the greeting as display text."""
        return f"Hello, {self.name}!"
