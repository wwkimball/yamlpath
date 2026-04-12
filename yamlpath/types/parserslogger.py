"""Define the required logging interface for parser helper methods."""
from typing import Any, Protocol


class ParsersLogger(Protocol):
    """Required logging interface for parser helper methods."""

    def debug(self, message: Any, **kwargs: Any) -> None:
        """Emit a DEBUG message."""

    def error(self, message: Any, exit_code: Any = None) -> None:
        """Emit an ERROR message."""
