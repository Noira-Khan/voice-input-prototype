"""Transcript shaping and public-setting measurement."""

from __future__ import annotations


def noisify(question: str, salt: int) -> tuple[str, list[list[str]]]:
    """Return a slightly misheard line and per-word alternatives.

    Demo speech uses this so a reviewer can fix one word without re-speaking.
    The original token is always one of the alternatives.
    """
    words = question.split()
    alts = [[word] for word in words]
    if not words:
        return question, alts
    idx = salt % len(words)
    original = words[idx]
    if len(original) <= 3 and len(words) > 1:
        idx = (idx + 1) % len(words)
        original = words[idx]
    if len(original) <= 3:
        return question, alts
    noisy = original[:-1]
    words[idx] = noisy
    alts[idx] = [noisy, original]
    return " ".join(words), alts


def alts_from_nbest(text: str, hypotheses: list[str]) -> list[list[str]]:
    """Align full-sentence hypotheses into per-word choices when lengths match."""
    words = text.split()
    alts = [[word] for word in words]
    for hypothesis in hypotheses:
        other = hypothesis.split()
        if len(other) != len(words):
            continue
        for index, token in enumerate(other):
            if token not in alts[index]:
                alts[index].append(token)
    return alts


def noise_bucket(noisy_place: bool, speech_level: float | None) -> str:
    """Collapse a simulation toggle and an optional mic level into a bucket.

    The noisy-place control is a prototype stand-in for on-device ambient
    measurement. When it is on, the bucket is loud even if the browser could
    not read a mic level.
    """
    if noisy_place:
        return "loud"
    if speech_level is None:
        return "quiet"
    if speech_level >= 55:
        return "loud"
    if speech_level >= 30:
        return "moderate"
    return "quiet"


def public_setting_flag(bucket: str, earphones: bool) -> bool:
    """True when the user is likely audible to people nearby.

    Earphones count as a private channel. Quiet rooms are not the drop-off
    setting this experiment is trying to measure.
    """
    return (not earphones) and bucket in {"moderate", "loud"}
