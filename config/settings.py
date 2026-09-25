"""Centralized, environment-configurable runtime settings."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """All user-adjustable values used by the current application."""

    transcription_model: str
    microphone_device: str | int | None
    sample_rate: int
    audio_channels: int
    minimum_recording_duration_seconds: float
    hotkey_label: str
    x11_primary_modifier_symbols: tuple[str, ...]
    x11_secondary_modifier_symbols: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load settings from .env/environment, falling back to safe defaults."""
        return cls(
            transcription_model=os.getenv(
                "VOICER_TRANSCRIPTION_MODEL", "gpt-transcribe"
            ),
            microphone_device=_optional_device("VOICER_MICROPHONE_DEVICE"),
            sample_rate=_positive_int("VOICER_SAMPLE_RATE", 16_000),
            audio_channels=_positive_int("VOICER_AUDIO_CHANNELS", 1),
            minimum_recording_duration_seconds=_positive_float(
                "VOICER_MIN_RECORDING_SECONDS", 0.15
            ),
            hotkey_label="Ctrl+Shift",
            x11_primary_modifier_symbols=("Control_L", "Control_R"),
            x11_secondary_modifier_symbols=("Shift_L", "Shift_R"),
        )


def _optional_device(name: str) -> str | int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    return int(value) if value.isdigit() else value


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


def _positive_float(name: str, default: float) -> float:
    value = float(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value

