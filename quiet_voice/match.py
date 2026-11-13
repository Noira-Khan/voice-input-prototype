"""Match a transcript to a fixed sample answer.

Both experiment arms call this. The prototype never generates a live model
answer, so a difference between Version A and Version B can only come from
the voice flow.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from quiet_voice.catalog import SAMPLES

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
MATCH_THRESHOLD = 0.42


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'")
    text = _PUNCT.sub(" ", text)
    return " ".join(text.split())


def score(query: str, sample: dict) -> float:
    normalized_query = normalize(query)
    ratio = SequenceMatcher(None, normalized_query, normalize(sample["q"])).ratio()
    hits = 0
    for keyword in sample["keywords"]:
        token = normalize(keyword)
        if token and token in normalized_query:
            hits += 1
    if hits >= 2:
        keyword_score = hits / max(1, min(3, len(sample["keywords"])))
    elif hits == 1:
        keyword_score = 0.2
    else:
        keyword_score = 0.0
    return max(ratio, keyword_score)


def match_answer(language: str, text: str) -> tuple[dict | None, list[str], float]:
    samples = SAMPLES.get(language) or SAMPLES["en"]
    ranked = sorted(((score(text, sample), sample) for sample in samples), reverse=True)
    best_score, best = ranked[0]
    questions = [sample["q"] for sample in samples]
    if best_score < MATCH_THRESHOLD:
        return None, questions, best_score
    return best, questions, best_score
