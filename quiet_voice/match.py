"""Match a transcript to a fixed sample answer.

Both experiment arms call this. The prototype never generates a live model
answer, so a difference between Version A and Version B can only come from
the voice flow.

A line that is only near a suggested question still counts. Hindi and
Hinglish suggestions are always in the search, because those are the
questions shown at the top of the chat.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from quiet_voice.catalog import SAMPLES

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_NUKTA = "\u093c"
MATCH_THRESHOLD = 0.42
NEAR_FLOOR = 0.34
_STOP = {
    "the",
    "and",
    "for",
    "with",
    "your",
    "mein",
    "aur",
    "kya",
    "ko",
    "se",
    "ka",
    "ki",
    "ke",
    "में",
    "से",
    "को",
    "और",
    "का",
    "की",
    "के",
    "एक",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower().replace("’", "'").replace("‘", "'"))
    text = text.replace(_NUKTA, "")
    text = unicodedata.normalize("NFC", text)
    text = _PUNCT.sub(" ", text)
    return " ".join(text.split())


def _content_tokens(text: str) -> set[str]:
    return {token for token in normalize(text).split() if len(token) > 2 and token not in _STOP}


def score(query: str, sample: dict) -> float:
    normalized_query = normalize(query)
    normalized_question = normalize(sample["q"])
    if not normalized_query or not normalized_question:
        return 0.0
    ratio = SequenceMatcher(None, normalized_query, normalized_question).ratio()
    if normalized_query in normalized_question or normalized_question in normalized_query:
        ratio = max(ratio, 0.92)
    query_tokens = set(normalized_query.split())
    content_tokens = _content_tokens(query)
    question_tokens = _content_tokens(sample["q"])
    shared = content_tokens & question_tokens
    coverage = len(shared) / max(1, len(question_tokens))
    jaccard = len(shared) / max(1, len(content_tokens | question_tokens))
    hits = 0
    longest = 0
    for keyword in sample["keywords"]:
        token = normalize(keyword)
        if not token or not _keyword_present(token, normalized_query, query_tokens):
            continue
        hits += 1
        longest = max(longest, len(token))
    if hits >= 2:
        keyword_score = min(1.0, 0.64 + 0.1 * (hits - 2))
    elif hits == 1 and longest >= 8:
        keyword_score = 0.56
    elif hits == 1:
        keyword_score = 0.22
    else:
        keyword_score = 0.0
    lexical = max(coverage, jaccard, keyword_score)
    if lexical < 0.2 and ratio < 0.72:
        ratio *= 0.45
    return max(ratio, lexical)


def _keyword_present(token: str, normalized_query: str, query_tokens: set[str]) -> bool:
    if token in query_tokens:
        return True
    if len(token) >= 5 and token in normalized_query:
        return True
    if len(token) < 4:
        return False
    return any(
        len(piece) >= 4 and SequenceMatcher(None, piece, token).ratio() >= 0.84
        for piece in query_tokens
    )


def _search_languages(language: str) -> list[str]:
    codes: list[str] = []
    for code in (language, "hi", "hinglish", "en"):
        if code in SAMPLES and code not in codes:
            codes.append(code)
    return codes


def match_answer(language: str, text: str) -> tuple[dict | None, list[str], float]:
    home = SAMPLES.get(language) or SAMPLES["en"]
    questions = [sample["q"] for sample in home]
    ranked: list[tuple[float, int, dict]] = []
    order = 0
    for code in _search_languages(language):
        for sample in SAMPLES[code]:
            ranked.append((score(text, sample), -order, sample))
            order += 1
    ranked.sort(reverse=True)
    best_score, _tie, best = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else 0.0
    nearest = best_score >= NEAR_FLOOR and (best_score - second_score) >= 0.05
    if best_score < MATCH_THRESHOLD and not nearest:
        return None, questions, best_score
    return best, questions, best_score
