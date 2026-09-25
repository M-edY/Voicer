"""Orchestrate push-to-talk microphone capture, transcription, and paste."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from asr.base import Transcriber
from audio.feedback import FeedbackPlayer
from audio.recorder import MicrophoneRecorder, Recording
from core.state import AppState
from input.base import TextInjector


class RecordingController:
    """Keep the hotkey callback responsive while transcription runs off-thread."""

    def __init__(
        self,
        recorder: MicrophoneRecorder,
        transcriber: Transcriber,
        injector: TextInjector | None = None,
        feedback_player: FeedbackPlayer | None = None,
    ) -> None:
        self._recorder = recorder
        self._transcriber = transcriber
        self._injector = injector
        self._feedback_player = feedback_player
        self._state = AppState.IDLE
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="asr")

    def on_ptt_down(self) -> None:
        if self._state is not AppState.IDLE:
            return
        if self._feedback_player is not None:
            self._feedback_player.play_recording_start()
        try:
            self._recorder.start()
        except Exception as error:
            print(f"Could not start microphone: {error}", flush=True)
            return

        self._state = AppState.LISTENING
        print("Recording… release Ctrl+Shift to transcribe.", flush=True)

    def on_ptt_up(self) -> None:
        if self._state is not AppState.LISTENING:
            return
        try:
            recording = self._recorder.stop()
        except Exception as error:
            self._state = AppState.IDLE
            print(f"Could not finish recording: {error}", flush=True)
            return

        if recording.duration_seconds < 0.15:
            recording.path.unlink(missing_ok=True)
            self._state = AppState.IDLE
            print("Recording was too short; discarded.", flush=True)
            return

        self._state = AppState.TRANSCRIBING
        print(f"Transcribing {recording.duration_seconds:.1f}s of microphone audio…")
        future = self._worker.submit(self._transcribe_and_clean, recording)
        future.add_done_callback(self._on_transcription_complete)

    def close(self) -> None:
        self._worker.shutdown(wait=False, cancel_futures=True)

    def _transcribe_and_clean(self, recording: Recording) -> str:
        try:
            return self._transcriber.transcribe(recording.path)
        finally:
            recording.path.unlink(missing_ok=True)

    def _on_transcription_complete(self, future: Future[str]) -> None:
        try:
            transcript = future.result()
            print(f"\nTranscript:\n{transcript}\n", flush=True)
            if self._injector is not None:
                self._injector.inject(transcript)
                print("Pasted into the active application.\n", flush=True)
        except Exception as error:
            print(f"\nTranscription or paste failed: {error}\n", flush=True)
        finally:
            self._state = AppState.IDLE
