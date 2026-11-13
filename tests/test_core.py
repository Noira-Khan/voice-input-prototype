"""Logic tests that do not need a browser or Streamlit server."""

from __future__ import annotations

import unittest
from pathlib import Path

from quiet_voice.catalog import LANGS, SAMPLES
from quiet_voice.events import EVENT_NAMES, make_event
from quiet_voice.match import match_answer
from quiet_voice.metrics import summarize
from quiet_voice.speech import noise_bucket, noisify, public_setting_flag

ROOT = Path(__file__).resolve().parents[1]
PROBLEM = (
    "Regional-language (Hindi, Hinglish and other) ChatGPT mobile users in India know about voice input "
    "— 25 of 27 surveyed (93%) have tried it — yet they report falling back to typing whenever other people are around. "
    "The blocker is social comfort, not discovery or accuracy: 52% feel awkward or self-conscious speaking to their phone "
    "in front of others, versus 33% who distrust accent recognition."
)


class CatalogTests(unittest.TestCase):
    def test_every_language_has_samples_and_copy(self):
        self.assertEqual(set(LANGS), set(SAMPLES))
        for code, samples in SAMPLES.items():
            self.assertGreaterEqual(len(samples), 4, code)
            for sample in samples:
                self.assertTrue(sample["q"].strip())
                self.assertTrue(sample["a"].strip())
                self.assertGreaterEqual(len(sample["keywords"]), 2)

    def test_problem_statement_is_unchanged_in_the_prd(self):
        prd = (ROOT / "docs" / "PRD.md").read_text(encoding="utf-8")
        self.assertIn(PROBLEM, prd.replace("\n", " "))

    def test_prd_lists_every_event(self):
        prd = (ROOT / "docs" / "PRD.md").read_text(encoding="utf-8")
        for name in EVENT_NAMES:
            self.assertIn(name, prd)


class MatchTests(unittest.TestCase):
    def test_exact_question_matches(self):
        sample, _questions, score = match_answer("en", "Explain photosynthesis simply")
        self.assertIsNotNone(sample)
        self.assertGreater(score, 0.9)
        self.assertIn("photosynthesis", sample["a"].lower())

    def test_noisy_prefix_still_matches(self):
        noisy, _alts = noisify("Explain photosynthesis simply", 0)
        sample, _questions, _score = match_answer("en", noisy)
        self.assertIsNotNone(sample)

    def test_keyword_pair_matches_hinglish_cooking(self):
        sample, _questions, _score = match_answer("hinglish", "aloo pyaaz recipe batao")
        self.assertIsNotNone(sample)
        self.assertIn("aloo", sample["a"].lower())

    def test_unrelated_text_returns_the_sample_list(self):
        sample, questions, _score = match_answer("en", "book a train to pune")
        self.assertIsNone(sample)
        self.assertGreaterEqual(len(questions), 4)


class SpeechTests(unittest.TestCase):
    def test_noisify_keeps_the_original_word_as_a_choice(self):
        question = "Explain photosynthesis simply"
        noisy, alts = noisify(question, 1)
        self.assertNotEqual(noisy, question)
        originals = question.split()
        self.assertTrue(any(original in choices for original, choices in zip(originals, alts)))

    def test_public_flag_needs_noise_and_no_earphones(self):
        self.assertTrue(public_setting_flag("loud", earphones=False))
        self.assertFalse(public_setting_flag("loud", earphones=True))
        self.assertFalse(public_setting_flag("quiet", earphones=False))
        self.assertEqual(noise_bucket(True, 10), "loud")
        self.assertEqual(noise_bucket(False, None), "quiet")
        self.assertEqual(noise_bucket(False, 40), "moderate")


class MetricTests(unittest.TestCase):
    def test_guardrail_fails_when_people_dismiss_the_prompt(self):
        events = [
            make_event("nudge_shown", "B", "hi"),
            make_event("nudge_shown", "B", "hi"),
            make_event("nudge_dismissed", "B", "hi"),
            make_event("transcript_latency_ms", "B", "hi", {"ms": 1800}),
            make_event("send_tapped", "B", "hi", {"channel": "voice"}),
        ]
        summary = summarize(events)
        self.assertFalse(summary["checks"]["prompt_dismiss_under_40"])
        self.assertTrue(summary["checks"]["latency_p90_under_2s"])
        self.assertFalse(summary["guardrail_pass"])

    def test_rerecord_does_not_count_as_abandonment(self):
        events = [
            make_event("transcript_review_shown", "B", "hi"),
            make_event("review_abandoned", "B", "hi", {"reason": "rerecord"}),
            make_event("send_tapped", "B", "hi", {"channel": "voice"}),
        ]
        summary = summarize(events)
        self.assertEqual(summary["abandoned"], 0)
        self.assertEqual(summary["send_completion"], 1)

    def test_public_retry_is_a_later_public_hold(self):
        events = [
            make_event("voice_hold_start", "B", "hi", {"public_setting_flag": True}),
            make_event("send_tapped", "B", "hi", {"channel": "voice"}),
            make_event("voice_hold_start", "B", "hi", {"public_setting_flag": True}),
            make_event("voice_hold_start", "B", "en", {"public_setting_flag": False}),
        ]
        summary = summarize(events)
        self.assertEqual(summary["public_attempts"], 2)
        self.assertEqual(summary["public_retries"], 1)

    def test_unknown_event_is_rejected(self):
        with self.assertRaises(ValueError):
            make_event("not_a_real_event", "A", None)


if __name__ == "__main__":
    unittest.main()
