# Implementation

How this repository maps to the PRD, how to exercise it, and how to extend it without breaking the experiment.

## Run

From the repository root, with Python 3.11 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest tests.test_core
streamlit run app.py
```

macOS or Linux use `source .venv/bin/activate` instead of the PowerShell activate script. Then open the URL Streamlit prints, usually `http://localhost:8501`.

Demo speech is the default. You do not need a microphone, an API key, or a GPU.

## Walk the quiet arm

1. Leave Version on **B**.
2. Read the prompt. Choose **Tap to try**, then a language. “Not now” hides the prompt and leaves the mic usable.
3. On the whisper screen, press and hold the circle, then release. Slide up before release to cancel. Space does the same from the keyboard once the circle is focused. **Release demo whisper** runs the identical result path if the iframe gesture is awkward.
4. On review, cycle the shortened word, try **Hide text until I tap it**, and send.
5. Confirm the win line, the streak, and the comfort check. Listen speaks only after the button.
6. Open the gear. The guardrail badge and `events.json` should include `nudge_shown`, `lang_picked`, `voice_hold_start`, `transcript_review_shown`, `send_tapped`, and `answer_shown`.

## Walk the control arm

Set Version to **A**. There is no prompt and no review. Tap the circle once to start and again to stop, or use **Release demo whisper**. The words are visible during a demo capture. The line lands in the composer. Send it. The answer matcher is the same. There is no streak and no comfort check.

Turn on **Noisy place**, leave earphones off, and complete a second hold after a send. The gear’s public-retry count should increase. Turn earphones on and the next hold should not count as public.

**After a long draft** waits until the composer has at least 60 characters before showing the prompt. **On open** is the default.

## Where behavior lives

| PRD behavior | Code |
| --- | --- |
| Prompt once, Version B only | `prompt_visible` and `maybe_log_nudge` in `app.py` |
| Language then recognizer | `LANGS` plus the `bcp47` argument to the mic |
| Hold, slide to cancel, hidden text, buzz | `components/quiet_mic/index.html` |
| Classic live text and beep | same file, `mode=classic` |
| Mandatory review | `open_review`, only when `version == "B"` |
| Word fix and edit-all | `cycle_word`, `apply_edit` |
| Hide text | `hide_text` checkbox, default from `hide_default` |
| Same answers in A and B | `match_answer` |
| Events and guardrails | `quiet_voice/events.py`, `quiet_voice/metrics.py` |
| Gear | `render_sidebar` |

## Add a language

1. Add the code to `LANGS` with a BCP-47 tag and `beta: True`.
2. Add a `UI` table. Missing keys fall back to English, but a shippable language should translate every key in the English table.
3. Add at least four `SAMPLES` with `q`, `a`, and two or more `keywords`. Include an English keyword where people code-mix, so “photosynthesis” still matches.
4. Run `python -m unittest tests.test_core`. The catalog test fails if a language has fewer than four samples.

Do not mark `beta` false until a native speaker has read the copy against the English source.

## Add a sample question

Append one object to that language’s list in `catalog.py`. Keep the answer short and factual. The matcher treats two keyword hits as a match, so choose keywords that do not appear in the other questions.

## Event rules

- Add the name to `EVENT_NAMES` or `make_event` will reject it. Also name it in `docs/PRD.md`; the test checks that the PRD lists every name.
- Write events from callbacks or from the single mic handler. Do not write them from a widget that reruns on every keystroke.
- `voice_hold_start` is recorded when the gesture ends, with `ts` set to the start time the iframe sent. The iframe cannot safely message Python at press-down without a rerun that would destroy the hold.
- Re-record uses `review_abandoned` with `reason=rerecord` so a correction is not punished by the send-completion guardrail.

## Tests

`tests/test_core.py` covers the matcher, the public-setting flag, the guardrail math, the catalog, and the presence of the original problem statement in the PRD. It does not open a browser.

The speech iframe needs a manual pass in Chrome or Edge:

- Demo hold shows dots, not words, in Version B, and reveals words in Version A.
- A short tap does not open review.
- Slide up cancels and stays on the whisper screen.
- Real speech returns a transcript only after the microphone permission is allowed.
- Firefox and Safari may have no `SpeechRecognition`. Demo mode is the supported path there.

## Known limits

- This is a desktop-width simulation of a phone flow, not an iOS or Android binary. Haptics often do nothing on a laptop.
- Web Speech quality is the browser’s, not a product model. Soft speech is not specially tuned.
- Latency in demo mode is a short simulated number. Real mode reports time from gesture start to recognizer end, which includes speaking time, so it is a prototype measurement rather than the production “after release” latency.
- Day-7 retention is a button in the gear. The prototype has no account and no next-day identity.
- Streaks reset when the session resets. “Simulate the next day” only moves the local date marker.
- Sample answers are deliberately narrow. An unmatched question lists the samples.
- Streamlit Community Cloud keeps session memory on the server for the life of the session. The app still does not write a database. Do not speak secrets into it.
