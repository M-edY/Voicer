#!/usr/bin/env python3
"""Record microphone audio with Ctrl+Shift, then print and paste its transcript."""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from asr.openai import OpenAITranscriber
from audio.feedback import FeedbackPlayer
from audio.recorder import MicrophoneRecorder
from core.recording_controller import RecordingController
from input.x11_hotkey import X11PushToTalk
from input.x11_injector import X11TextInjector


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record with Ctrl+Shift, then print and paste the transcript."
    )
    parser.add_argument("--model", default="gpt-transcribe")
    parser.add_argument("--device", help="Optional sounddevice microphone name or ID.")
    parser.add_argument("--sample-rate", type=int, default=16_000)
    args = parser.parse_args()

    load_dotenv()
    recorder = MicrophoneRecorder(
        sample_rate=args.sample_rate,
        device=args.device,
    )
    controller = RecordingController(
        recorder=recorder,
        transcriber=OpenAITranscriber(model=args.model),
        injector=X11TextInjector(),
        feedback_player=FeedbackPlayer(),
    )
    hotkey = X11PushToTalk(controller.on_ptt_down, controller.on_ptt_up)
    try:
        hotkey.run()
    finally:
        controller.close()


if __name__ == "__main__":
    main()
