# Software required

Everything below is enough to run the prototype locally and to host it on Streamlit Community Cloud. No paid API is required.

## Required

| Software | Version | Why |
| --- | --- | --- |
| Python | 3.11, 3.12, or 3.13 | Runs the app. Streamlit Cloud is pinned to 3.12 via `runtime.txt`. |
| pip | current | Installs `requirements.txt`. |
| Streamlit | 1.58.0, pinned | UI, session state, and the custom mic component. |
| A Chromium browser | current Chrome or Edge | Required only for **Real** speech (`webkitSpeechRecognition`). |
| Git | 2.x | Clone and update this repository. |

Install:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Check:

```powershell
python -m unittest tests.test_core
streamlit run app.py
```

## Browser behavior

| Browser | Demo speech | Real speech | Listen |
| --- | --- | --- | --- |
| Chrome, Edge | Yes | Yes, after microphone permission | Yes, with whatever voices the OS has |
| Firefox, Safari | Yes | Usually no recognizer | Sometimes |

Real speech sends audio to the browser vendor’s speech service. This prototype does not add its own speech vendor and does not store audio. Disclose that if you put the app in front of participants.

Listen uses the browser `speechSynthesis` API. A language with no installed voice falls back to the default voice. That is a device limit, not an app bug.

## Not required

- OpenAI or any other model key. Answers are the fixed samples in `quiet_voice/catalog.py`.
- A GPU, Whisper, or ffmpeg.
- A database, Redis, or Docker.
- Node.js. The mic component is one HTML file. It is not a compiled frontend.
- A phone. The flow is usable with a mouse or keyboard. A phone is still the right device for the Week 4 comfort test, because haptics and social comfort do not show up on a laptop.

## Streamlit Community Cloud

The app is meant to be deployed from this GitHub repository.

1. Push `main`. The entry file is `app.py`. Dependencies are `requirements.txt`. Python is `runtime.txt`.
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with the GitHub account that can read `Noira-Khan/voice-input-prototype`.
3. Create a new app. Repository `Noira-Khan/voice-input-prototype`, branch `main`, main file path `app.py`.
4. Deploy. The first build installs Streamlit and boots the process. There are no secrets to paste.
5. Open the app URL and run the demo path in `docs/IMPLEMENTATION.md` once on the public URL. Community Cloud serves the mic iframe from the same app, which is what the microphone permission needs.

Reboot the app from the Cloud dashboard after later pushes if the new commit does not appear on its own.

Local `streamlit run` and Cloud use the same code. Cloud will not add a database. Each visitor gets a session log that disappears when the session ends.

## Optional

| Software | Use |
| --- | --- |
| VS Code or Cursor | Editing. |
| Chrome DevTools | If a real-speech transcript comes back empty, check the iframe console for a recognizer error. |
| A second browser profile | One profile on Version A and one on Version B, so the two arms are not the same session. |

## Repository layout

```
app.py
requirements.txt
runtime.txt
.streamlit/config.toml
components/quiet_mic/index.html
quiet_voice/
tests/test_core.py
docs/PRD.md
docs/ARCHITECTURE.md
docs/IMPLEMENTATION.md
docs/SOFTWARE.md
```
