"""Platform-neutral contract for placing transcribed text in another app."""

from typing import Protocol


class TextInjector(Protocol):
    """Place text into the currently focused application."""

    def inject(self, text: str) -> None:
        """Paste text without submitting or otherwise executing it."""
