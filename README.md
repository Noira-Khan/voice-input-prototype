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

Speech starts on **Real**. Chrome or Edge can use the microphone. No API key. Firefox has no recognizer, so switch Speech to **Demo** in the gear.

1. Stay on Version **B**. The opening screen is the chat. It does not list sample questions.
2. Tap the mic and pick a language, then hold to speak.
3. Under the message bar there are two suggestions, one Hindi and one Hinglish. Say one, or something close to any sample question, then review and send.
4. Use the gear for Version A, Demo speech, a noisy-place flag, the guardrail badge, and `events.json`.

## Docs

- [Product requirements](docs/PRD.md) — the problem statement is unchanged; the flow, metrics, and prototype scope are tightened
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation](docs/IMPLEMENTATION.md)
- [Software required, and Streamlit Cloud](docs/SOFTWARE.md)

## What the two arms do

**B · Quiet push-to-talk.** One language prompt, hold to speak, words hidden, buzz instead of a chime, review before send, then a streak and a comfort check.

**A · Current voice.** No prompt and no review. Words show while you speak. The same sample answers come back, so a difference is the voice flow and not the reply.

The opening screen stays a chat. Two suggestions, one Hindi and one Hinglish, sit under the message bar. The matcher still checks every sample, so a spoken line that is only near one of them returns that answer.

Regional copy is a first-pass beta. It needs a native-speaker review before anyone treats it as final.

## Tests

```powershell
python -m unittest tests.test_core
```

## Deploy

Streamlit Community Cloud: repository `Noira-Khan/voice-input-prototype`, branch `main`, main file `app.py`. Details are in [docs/SOFTWARE.md](docs/SOFTWARE.md).
