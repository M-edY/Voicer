"""Paste text into the currently focused X11 application."""

from __future__ import annotations

import os
import shutil
import subprocess


class X11TextInjector:
    """Copy text to CLIPBOARD, then send Ctrl+V to the active X11 window."""

    def inject(self, text: str) -> None:
        if not text:
            return
        if not os.environ.get("DISPLAY"):
            raise RuntimeError("DISPLAY is not set, so text cannot be pasted on X11.")
        if not shutil.which("xclip"):
            raise RuntimeError("xclip is required to copy the transcript to CLIPBOARD.")
        if not shutil.which("xdotool"):
            raise RuntimeError(
                "xdotool is required to paste text on X11. Install it with "
                "'sudo apt install xdotool'."
            )

        subprocess.run(
            ["xclip", "-selection", "clipboard", "-in"],
            input=text,
            text=True,
            check=True,
        )
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
            check=True,
        )
