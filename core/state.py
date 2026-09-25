"""States for the first push-to-talk transcription flow."""

from enum import Enum, auto


class AppState(Enum):
    IDLE = auto()
    LISTENING = auto()
    TRANSCRIBING = auto()
