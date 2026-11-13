"""What a greeting is and how it reads."""

from dataclasses import dataclass

DEFAULT_NAME = "world"


@dataclass(frozen=True, slots=True)
class Greeting:
    """A greeting addressed to someone."""

    name: str

    def message(self) -> str:
        """Return the greeting as display text."""
        return f"Hello, {self.name}!"
