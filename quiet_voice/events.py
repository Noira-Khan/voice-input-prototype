"""Client event schema for the Quiet Voice prototype."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

# Names match the experiment taxonomy in docs/PRD.md.
EVENT_NAMES = (
    "nudge_shown",
    "nudge_accepted",
    "nudge_dismissed",
    "lang_picked",
    "voice_hold_start",
    "voice_cancel",
    "transcript_review_shown",
    "word_edited",
    "sample_question_picked",
    "hide_text_toggled",
    "send_tapped",
    "review_abandoned",
    "noise_bucket",
    "speech_level",
    "answer_shown",
    "voice_return_d7",
    "comfort_survey_response",
    "transcript_latency_ms",
)


def make_event(name: str, version: str, language: str | None, props: dict | None = None, ts: str | None = None) -> dict:
    if name not in EVENT_NAMES:
        raise ValueError(f"Unknown event {name}")
    return {
        "id": str(uuid4()),
        "name": name,
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "version": version,
        "language": language,
        "props": props or {},
    }
