"""X11 global push-to-talk listener backed by xinput."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable


EVENT_RE = re.compile(r"EVENT type (2|3) \((KeyPress|KeyRelease)\)")
DETAIL_RE = re.compile(r"^\s*detail:\s*(\d+)")
KEYMAP_RE = re.compile(r"^\s*(\d+)\s+.*\(([^)]+)\)")


class X11PushToTalk:
    """Observe Ctrl+Shift globally without consuming the shortcut."""

    def __init__(self, on_down: Callable[[], None], on_up: Callable[[], None]) -> None:
        self._on_down = on_down
        self._on_up = on_up

    def run(self) -> None:
        self._validate_environment()
        ctrl_codes = self._keycodes_for("Control_L", "Control_R")
        shift_codes = self._keycodes_for("Shift_L", "Shift_R")
        if not ctrl_codes or not shift_codes:
            raise RuntimeError("Could not resolve Ctrl or Shift in the X11 keymap.")

        print("Ready: hold Ctrl+Shift to record and transcribe. Ctrl+C quits.")
        command = ["xinput", "test-xi2", "--root"]
        if shutil.which("stdbuf"):
            command = ["stdbuf", "-oL", *command]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        held: set[int] = set()
        ptt_active = False
        event_kind: str | None = None

        try:
            assert process.stdout is not None
            for line in process.stdout:
                event_match = EVENT_RE.search(line)
                if event_match:
                    event_kind = event_match.group(2)
                    continue

                detail_match = DETAIL_RE.match(line)
                if not detail_match or event_kind is None:
                    continue

                keycode = int(detail_match.group(1))
                if event_kind == "KeyPress":
                    held.add(keycode)
                else:
                    held.discard(keycode)

                shortcut_held = bool(held & ctrl_codes) and bool(held & shift_codes)
                if shortcut_held and not ptt_active:
                    ptt_active = True
                    self._on_down()
                elif ptt_active and not shortcut_held:
                    ptt_active = False
                    self._on_up()
                event_kind = None
        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()

    @staticmethod
    def _validate_environment() -> None:
        if os.environ.get("XDG_SESSION_TYPE", "").lower() != "x11":
            raise RuntimeError("X11PushToTalk requires an X11 session.")
        if not os.environ.get("DISPLAY"):
            raise RuntimeError("DISPLAY is not set, so this process cannot use X11.")
        if not shutil.which("xinput") or not shutil.which("xmodmap"):
            raise RuntimeError("xinput and xmodmap must be installed.")

    @staticmethod
    def _keycodes_for(*symbols: str) -> set[int]:
        result = subprocess.run(
            ["xmodmap", "-pk"], check=True, capture_output=True, text=True
        )
        desired = set(symbols)
        return {
            int(match.group(1))
            for line in result.stdout.splitlines()
            if (match := KEYMAP_RE.match(line)) and match.group(2) in desired
        }
