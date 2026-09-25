"""Provider-independent speech transcription contract."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class Transcriber(Protocol):
    """Convert a completed audio recording into plain text."""

    def transcribe(self, audio_path: Path) -> str:
        """Return the transcript for a local audio file."""
