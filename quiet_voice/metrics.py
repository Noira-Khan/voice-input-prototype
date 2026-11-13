"""In-session summaries for the researcher console.

Production metrics are defined in docs/PRD.md. This module computes the same
signals from one prototype session so a test can be inspected before export.
"""

from __future__ import annotations


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = fraction * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return float(ordered[low] * (1 - weight) + ordered[high] * weight)


def _named(events: list[dict], name: str) -> list[dict]:
    return [event for event in events if event.get("name") == name]


def summarize(events: list[dict]) -> dict:
    shown = _named(events, "nudge_shown")
    dismissed = _named(events, "nudge_dismissed")
    sends = _named(events, "send_tapped")
    abandoned = [
        event
        for event in _named(events, "review_abandoned")
        if event.get("props", {}).get("reason") != "rerecord"
    ]
    latencies = [
        float(event["props"]["ms"])
        for event in _named(events, "transcript_latency_ms")
        if "ms" in event.get("props", {})
    ]
    holds = _named(events, "voice_hold_start")
    public_holds = [event for event in holds if event.get("props", {}).get("public_setting_flag")]
    send_index = next((index for index, event in enumerate(events) if event.get("name") == "send_tapped"), None)
    public_retries = 0
    if send_index is not None:
        public_retries = sum(
            1
            for event in events[send_index + 1 :]
            if event.get("name") == "voice_hold_start" and event.get("props", {}).get("public_setting_flag")
        )

    dismiss_rate = (len(dismissed) / len(shown)) if shown else None
    voice_reviews = len(_named(events, "transcript_review_shown"))
    send_completion = None
    if sends or abandoned:
        send_completion = len(sends) / (len(sends) + len(abandoned))
    latency_p90 = percentile(latencies, 0.9)

    dismiss_ok = dismiss_rate is None or dismiss_rate < 0.4
    latency_ok = latency_p90 is None or latency_p90 <= 2000
    send_ok = send_completion is None or send_completion >= 0.8

    return {
        "nudge_shown": len(shown),
        "nudge_dismissed": len(dismissed),
        "dismiss_rate": dismiss_rate,
        "voice_reviews": voice_reviews,
        "sends": len(sends),
        "abandoned": len(abandoned),
        "send_completion": send_completion,
        "latency_p90_ms": latency_p90,
        "public_attempts": len(public_holds),
        "public_retries": public_retries,
        "comfort_responses": len(_named(events, "comfort_survey_response")),
        "guardrail_pass": dismiss_ok and latency_ok and send_ok,
        "checks": {
            "prompt_dismiss_under_40": dismiss_ok,
            "latency_p90_under_2s": latency_ok,
            "send_completion_not_fallen": send_ok,
        },
    }
