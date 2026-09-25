"""Capture a bounded mono PCM recording from the default microphone."""

from __future__ import annotations

import tempfile
import threading
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Recording:
    path: Path
    duration_seconds: float


class MicrophoneRecorder:
    """Start on push-to-talk down and produce a temporary WAV on release."""

    def __init__(
        self,
        sample_rate: int = 16_000,
        channels: int = 1,
        device: str | int | None = None,
    ) -> None:
        self._sample_rate = sample_rate
        self._channels = channels
        self._device = device
        self._chunks: list[bytes] = []
        self._lock = threading.Lock()
        self._stream: Any | None = None

    def start(self) -> None:
        if self._stream is not None:
            raise RuntimeError("Microphone recording is already active.")

        try:
            import sounddevice as sd
        except ImportError as error:
            raise RuntimeError(
                "Microphone capture requires sounddevice. Install it with "
                "'.venv/bin/python -m pip install sounddevice'."
            ) from error

        with self._lock:
            self._chunks.clear()

        self._stream = sd.RawInputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="int16",
            device=self._device,
            callback=self._on_audio,
        )
        self._stream.start()

    def stop(self) -> Recording:
        if self._stream is None:
            raise RuntimeError("Microphone recording is not active.")

        stream, self._stream = self._stream, None
        try:
            stream.stop()
        finally:
            stream.close()

        with self._lock:
            pcm = b"".join(self._chunks)
            self._chunks.clear()

        bytes_per_second = self._sample_rate * self._channels * 2
        duration_seconds = len(pcm) / bytes_per_second
        if not pcm:
            raise RuntimeError("The microphone produced no audio.")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary:
            path = Path(temporary.name)

        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(self._channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(pcm)

        return Recording(path=path, duration_seconds=duration_seconds)

    def _on_audio(self, indata: Any, frames: int, time: Any, status: Any) -> None:
        if status:
            print(f"Microphone status: {status}", flush=True)
        with self._lock:
            self._chunks.append(bytes(indata))
