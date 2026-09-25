"""Optional audio feedback for push-to-talk actions."""

from __future__ import annotations

import os
import time
import warnings
from pathlib import Path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
    module="pygame.pkgdata",
)

import pygame


SOUND_PATH = Path(__file__).resolve().parent.parent / "assets/sounds/start_rec_FX.mp3"


class FeedbackPlayer:
    """Play the bundled recording-start cue without blocking Voicer on errors."""

    def __init__(self) -> None:
        self._available = False
        try:
            pygame.mixer.init()
            self._available = SOUND_PATH.is_file()
        except pygame.error:
            pass

    def play_recording_start(self) -> None:
        """Play the cue before recording, so speaker audio is not transcribed."""
        if not self._available:
            return

        try:
            pygame.mixer.music.load(str(SOUND_PATH))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.01)
        except (OSError, pygame.error):
            return
