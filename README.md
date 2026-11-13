# Quiet Voice Mode

Research prototype for regional-language ChatGPT mobile users who have already tried voice and go back to typing when other people are around. The blocker is social comfort: in the Milestone 2 interviews, 52% felt awkward speaking to their phone in front of others, against 33% who distrusted accent recognition.

This repository replaces the earlier static HTML walkthrough with a Streamlit app you can run and host.

## Try it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Demo speech is on by default. No microphone and no API key.

1. Stay on Version **B**.
2. Tap the prompt, pick a language, then hold the mic or press **Release demo whisper**.
3. Fix the shortened word, hide the text if you want, and send.
4. Use the gear for Version A, a noisy-place flag, the guardrail badge, and `events.json`.

Chrome or Edge can switch Speech to **Real**. Firefox can stay on Demo.

## Docs

- [Product requirements](docs/PRD.md) — the problem statement is unchanged; the flow, metrics, and prototype scope are tightened
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation](docs/IMPLEMENTATION.md)
- [Software required, and Streamlit Cloud](docs/SOFTWARE.md)

## What the two arms do

**B · Quiet push-to-talk.** One language prompt, hold to speak, words hidden, buzz instead of a chime, review before send, then a streak and a comfort check.

**A · Current voice.** No prompt and no review. Words show while you speak. The same sample answers come back, so a difference is the voice flow and not the reply.

Regional copy is a first-pass beta. It needs a native-speaker review before anyone treats it as final.

## Tests

```powershell
python -m unittest tests.test_core
```

## Deploy

Streamlit Community Cloud: repository `Noira-Khan/voice-input-prototype`, branch `main`, main file `app.py`. Details are in [docs/SOFTWARE.md](docs/SOFTWARE.md).
