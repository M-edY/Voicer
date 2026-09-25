"""OpenAI implementation of the transcription contract."""

from __future__ import annotations

from pathlib import Path

from openai import OpenAI


class OpenAITranscriber:
    """Transcribe completed recordings with OpenAI's audio API."""

    def __init__(self, model: str = "gpt-transcribe") -> None:
        self._client = OpenAI()
        self._model = model

    def transcribe(self, audio_path: Path) -> str:
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

        with audio_path.open("rb") as audio_file:
            response = self._client.audio.transcriptions.create(
                model=self._model,
                file=audio_file,
            )

        return response.text.strip()
