# Architecture

Quiet Voice Mode is a single Streamlit process. The browser does the speech work. The Python process owns the screen, the sample answers, and the event log. There is no database and no model API.

```mermaid
flowchart LR
  subgraph browser [Browser]
    Phone[Streamlit screens]
    Mic[quiet_mic iframe]
    Speech[Web Speech API]
    Talk[speechSynthesis]
  end
  subgraph server [Streamlit server]
    State[session_state]
    Match[sample matcher]
    Metrics[guardrail summary]
  end
  Phone --> State
  Mic -->|one message per gesture| State
  Mic --> Speech
  State --> Match
  State --> Metrics
  Phone --> Talk
```

## Why the mic is an iframe

Streamlit reruns the Python script on every widget change. A press-and-hold gesture cannot survive that rerun if the button lives in Python. The hold, the slide-to-cancel, the live-versus-hidden transcript, and the beep-versus-buzz contrast stay inside `components/quiet_mic/index.html`. The iframe posts one JSON value when the gesture ends. Python reruns then, and only then.

The iframe is allowed to use the microphone by Streamlit’s component permissions. Real speech still depends on a Chromium browser that exposes `webkitSpeechRecognition`. Demo speech never calls it.

A second `getUserMedia` stream is intentionally not opened. On Chrome it competes with the recognizer and can return an empty transcript. Noise and earphone state come from the gear instead.

## Modules

| Path | Responsibility |
| --- | --- |
| `app.py` | Screens, gear, session state, when events are written |
| `components/quiet_mic/index.html` | Hold / tap gesture, Web Speech, demo mishear playback |
| `quiet_voice/catalog.py` | Languages, beta copy, fixed questions and answers |
| `quiet_voice/match.py` | Shared matcher used by Version A and Version B |
| `quiet_voice/speech.py` | Demo mishear, n-best alignment, noise bucket, public-setting flag |
| `quiet_voice/events.py` | Allowed event names and the event shape |
| `quiet_voice/metrics.py` | Session guardrail math for the gear |
| `docs/` | PRD, this architecture, the implementation notes, and the software list |

## Session state

One Streamlit session is one participant. Refreshing the tab starts over. Reset does the same.

Important keys:

- `version` — `A` or `B`
- `language_choice` — `unset` or a language code
- `screen` — `chat`, `language`, `listen`, or `review`
- `messages` — the thread, including fixed answers
- `review` — words, alternatives, and latency for the open review
- `events` — the append-only log
- `speech_mode` — `Demo` or `Real`
- `noisy`, `earphones`, `hide_default` — measurement and privacy switches
- `streak`, `streak_date` — Version B reinforcement, local to the session

Widget-backed keys are changed from button callbacks, which Streamlit runs before the next script pass. That avoids writing a widget value after the widget has already been drawn.

## Arms

Both arms call `match_answer`. Version B must pass through review before `send_tapped` with `channel=voice`. Version A puts the transcript in the composer and waits for Send. The win banner, the streak, and the comfort check run only in Version B, so the control arm does not receive the reinforcement it is supposed to lack.

## Matching

`match_answer` scores the transcript against that language’s samples with `SequenceMatcher`, and also with keyword hits. Two keyword hits are enough for a short code-mixed line such as “aloo pyaaz”. Below the threshold the user sees the sample list, not a generated answer.

## Measurement

`public_setting_flag` is true only when the bucket is `moderate` or `loud` and earphones are out. “Noisy place” forces the bucket to `loud`, which is how a desk test can still produce a public-setting event. This flag never changes the screen. It only changes the log.

## Failure behavior

| Failure | What the person sees |
| --- | --- |
| Browser has no Web Speech | The whisper screen says so. Demo speech still completes the flow. |
| Hold was under half a second | “Hold a little longer.” Nothing is logged as a send. |
| Slide up or Escape | Cancel event. The whisper screen stays up. |
| Empty real transcript | A plain error, no review, no send. |
| Question outside the sample set | The list of sample questions. |
| Recognizer returns one hypothesis | Review still opens. Edit-all is the fix path. |

## What this is not

This is not the ChatGPT client. It does not call an OpenAI API, does not train a model, and does not detect a real room. Haptics vibrate only on phones that allow `navigator.vibrate`. Desktop buzz is a no-op, which the chip still explains.
