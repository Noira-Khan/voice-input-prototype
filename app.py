"""Quiet Voice Mode — Streamlit research prototype.

Run: streamlit run app.py
"""

from __future__ import annotations

import html
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from quiet_voice.catalog import LANGS, SAMPLES, ui
from quiet_voice.events import make_event
from quiet_voice.match import match_answer
from quiet_voice.metrics import summarize
from quiet_voice.speech import alts_from_nbest, noise_bucket, noisify, public_setting_flag

MIC = components.declare_component(
    "quiet_mic",
    path=str(Path(__file__).resolve().parent / "components" / "quiet_mic"),
)

st.set_page_config(
    page_title="ChatGPT",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
          html, body, [class*="css"] {
            font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
          }
          .stApp { background: #ffffff; color: #0d0d0d; }
          header[data-testid="stHeader"] { background: rgba(255,255,255,.85); }
          section.main > div.block-container { max-width: 760px; padding-top: .4rem; }
          [data-testid="stSidebar"] { background: #f9f9f9; border-right: 1px solid #ececec; }
          footer { visibility: hidden; }
          .gpt-top { text-align: center; padding: 4px 0 18px; }
          .gpt-name { font-weight: 650; font-size: 1.05rem; letter-spacing: -0.01em; }
          .gpt-sub { color: #8e8ea0; font-size: .8rem; margin-top: 2px; }
          .gpt-empty { text-align: center; padding: 16vh 12px 6vh; }
          .gpt-suggest-label {
            font-size: .78rem; font-weight: 650; letter-spacing: .02em;
            color: #6e6e80; margin: 2px 0 6px;
          }
          .gpt-mark {
            width: 42px; height: 42px; border-radius: 50%; background: #0d0d0d; margin: 0 auto 14px;
          }
          .gpt-mark.sm { width: 28px; height: 28px; margin: 2px 0 0; flex: none; }
          .gpt-empty h2 { font-weight: 480; font-size: 1.7rem; margin: 0; letter-spacing: -0.02em; }
          .gpt-user-row { display: flex; justify-content: flex-end; margin: 14px 0; }
          .gpt-user {
            max-width: min(80%, 520px);
            background: #f4f4f4;
            color: #0d0d0d;
            border-radius: 22px;
            padding: 10px 16px;
            line-height: 1.5;
          }
          .gpt-ai { display: flex; gap: 14px; align-items: flex-start; margin: 18px 0 4px; }
          .gpt-ai-body { line-height: 1.6; padding-top: 2px; }
          .gpt-suggest {
            border: 1px solid #ececec;
            border-radius: 18px;
            padding: 12px 14px;
            margin: 12px 0;
            background: #fff;
          }
          .gpt-suggest strong { display: block; margin-bottom: 4px; }
          .gpt-suggest p, .gpt-suggest small { margin: 0; color: #6e6e80; }
          .gpt-note { color: #6e6e80; font-size: .95rem; margin: 4px 0 12px 42px; }
          .gpt-screen-title { font-size: 1.25rem; font-weight: 600; margin: 8px 0 4px; letter-spacing: -0.02em; }
          .gpt-muted { color: #8e8ea0; font-size: .9rem; margin-bottom: 10px; }
          .gpt-blur {
            filter: blur(8px); user-select: none; background: #f4f4f4;
            border-radius: 22px; padding: 14px 16px;
          }
          .gpt-transcript {
            background: #f4f4f4; border-radius: 22px; padding: 14px 16px;
            font-size: 1.02rem; line-height: 1.5;
          }
          section.main [data-testid="stBaseButton-primary"] {
            background: #0d0d0d; color: #fff; border: none; border-radius: 999px;
          }
          section.main [data-testid="stBaseButton-secondary"] {
            background: #fff; color: #0d0d0d; border: 1px solid #e5e5e5; border-radius: 999px;
          }
          section.main [data-testid="stTextInput"] input {
            border-radius: 26px;
            border: 1px solid #e3e3e3;
            background: #fff;
            min-height: 52px;
            padding-left: 18px;
            box-shadow: 0 8px 24px rgba(0,0,0,.04);
          }
          section.main [data-testid="stTextArea"] textarea {
            border-radius: 16px;
            border: 1px solid #e5e5e5;
            background: #fff;
          }
          div[data-testid="stAlert"] { border-radius: 14px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if st.session_state.get("do_reset"):
        st.session_state.clear()
    defaults = {
        "version": "B",
        "language_choice": "unset",
        "language_prev": "unset",
        "speech_mode": "Real",
        "noisy": False,
        "earphones": False,
        "hide_default": False,
        "prompt_timing": "On open",
        "screen": "chat",
        "messages": [],
        "events": [],
        "seen_ids": [],
        "prompt_dismissed": False,
        "prompt_accepted": False,
        "nudge_logged": False,
        "review": None,
        "streak": 0,
        "streak_date": None,
        "comfort_open": False,
        "show_win": False,
        "demo_i": 0,
        "draft_from_voice": False,
        "d7_marked": False,
        "epoch": 0,
        "flash": None,
        "hide_text": False,
        "hide_text_prev": False,
        "speech_real_default": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if not st.session_state.speech_real_default:
        st.session_state.speech_mode = "Real"
        st.session_state.speech_real_default = True


def event_language() -> str | None:
    choice = st.session_state.language_choice
    return None if choice == "unset" else choice


def effective_lang() -> str:
    choice = st.session_state.language_choice
    return choice if choice in LANGS else "en"


def text(key: str) -> str:
    return ui(effective_lang(), key)


def log(name: str, ts: str | None = None, **props) -> None:
    st.session_state.events.append(
        make_event(name, st.session_state.version, event_language(), props, ts=ts)
    )


def iso_from_ms(millis: int | float | None) -> str | None:
    if not millis:
        return None
    return datetime.fromtimestamp(millis / 1000, timezone.utc).isoformat()


def prompt_visible() -> bool:
    if st.session_state.version != "B":
        return False
    if st.session_state.prompt_dismissed or st.session_state.prompt_accepted:
        return False
    if st.session_state.screen != "chat":
        return False
    if st.session_state.prompt_timing == "On open":
        return True
    return len(st.session_state.get("draft") or "") >= 60


def maybe_log_nudge() -> None:
    if prompt_visible() and not st.session_state.nudge_logged:
        log("nudge_shown", timing=st.session_state.prompt_timing)
        st.session_state.nudge_logged = True


def sync_language() -> None:
    current = st.session_state.language_choice
    previous = st.session_state.language_prev
    if current != "unset" and current != previous:
        log("lang_picked", language=current)
    st.session_state.language_prev = current


def ask_suggestion(language: str, question: str) -> None:
    sample = next(item for item in SAMPLES[language] if item["q"] == question)
    st.session_state.messages.append({"role": "user", "text": question, "channel": "sample"})
    st.session_state.messages.append({"role": "assistant", "text": sample["a"], "channel": "sample"})
    log("sample_question_picked", question=question)
    log("answer_shown", channel="sample", matched=True)
    st.session_state.screen = "chat"


def answer_for(language: str, transcript: str) -> tuple[str, bool]:
    sample, questions, _score = match_answer(language, transcript)
    if sample:
        return sample["a"], True
    heard = ui(language, "heard").replace("{text}", transcript)
    lines = [heard, "", ui(language, "no_match_intro"), ""]
    lines.extend(f"- {question}" for question in questions)
    return "\n".join(lines), False


def bump_streak() -> None:
    today = date.today().isoformat()
    if st.session_state.streak_date != today:
        st.session_state.streak += 1
        st.session_state.streak_date = today


def deliver(transcript: str, channel: str) -> None:
    language = effective_lang()
    answer, matched = answer_for(language, transcript)
    st.session_state.messages.append({"role": "user", "text": transcript, "channel": channel})
    st.session_state.messages.append({"role": "assistant", "text": answer, "channel": channel})
    log("answer_shown", channel=channel, matched=matched)
    if channel == "voice" and st.session_state.version == "B":
        bump_streak()
        st.session_state.comfort_open = True
        st.session_state.show_win = True


def measurement(speech_level) -> dict:
    bucket = noise_bucket(st.session_state.noisy, speech_level)
    return {
        "bucket": bucket,
        "earphone_status": "in" if st.session_state.earphones else "out",
        "public_setting_flag": public_setting_flag(bucket, st.session_state.earphones),
        "speech_level": speech_level,
    }


def open_review(transcript: str, alts: list[list[str]], latency_ms: int, speech_level) -> None:
    words = transcript.split()
    if len(alts) != len(words):
        alts = [[word] for word in words]
    st.session_state.review = {
        "text": " ".join(words),
        "words": words,
        "alts": alts,
        "latency_ms": int(latency_ms or 0),
    }
    hidden = bool(st.session_state.hide_default)
    st.session_state.hide_text = hidden
    st.session_state.hide_text_prev = hidden
    st.session_state.edit_all_text = " ".join(words)
    st.session_state.screen = "review"
    log("transcript_review_shown")


def record_hold(event: dict, outcome: str) -> dict:
    measured = measurement(event.get("speechLevel"))
    start_ts = iso_from_ms(event.get("startedAt"))
    log(
        "voice_hold_start",
        ts=start_ts,
        mode="quiet" if st.session_state.version == "B" else "classic",
        speech=st.session_state.speech_mode.lower(),
        outcome=outcome,
        **measured,
    )
    log(
        "noise_bucket",
        bucket=measured["bucket"],
        earphone_status=measured["earphone_status"],
        public_setting_flag=measured["public_setting_flag"],
    )
    if measured["speech_level"] is not None:
        log("speech_level", level=measured["speech_level"])
    return measured


def apply_mic_event(event: dict) -> None:
    kind = event.get("type")
    if kind == "too_short":
        st.session_state.flash = text("too_short")
        return
    if kind == "cancel":
        record_hold(event, "cancel")
        log("voice_cancel")
        st.session_state.flash = text("cancelled")
        return
    if kind == "error":
        st.session_state.flash = event.get("message") or text("no_speech")
        return
    if kind != "result":
        return
    record_hold(event, "result")
    latency = int(event.get("latencyMs") or 0)
    log("transcript_latency_ms", ms=latency)
    transcript = (event.get("transcript") or "").strip()
    if not transcript:
        st.session_state.flash = text("no_speech")
        return
    if event.get("alts"):
        alts = event["alts"]
    else:
        alts = alts_from_nbest(transcript, event.get("alternatives") or [])
    if st.session_state.version == "B":
        open_review(transcript, alts, latency, event.get("speechLevel"))
    else:
        st.session_state.draft = transcript
        st.session_state.draft_from_voice = True
        st.session_state.screen = "chat"
        st.session_state.flash = "Transcript is in the box. Send when you are ready."
    if st.session_state.speech_mode == "Demo":
        st.session_state.demo_i += 1


def demo_payload() -> tuple[str, list]:
    samples = SAMPLES[effective_lang()]
    sample = samples[st.session_state.demo_i % len(samples)]
    return noisify(sample["q"], st.session_state.demo_i)


def remember(event) -> bool:
    if not isinstance(event, dict) or "id" not in event:
        return False
    if event["id"] in st.session_state.seen_ids:
        return False
    st.session_state.seen_ids.append(event["id"])
    st.session_state.seen_ids = st.session_state.seen_ids[-40:]
    return True


def release_demo() -> None:
    transcript, alts = demo_payload()
    apply_mic_event(
        {
            "id": f"demo-{st.session_state.demo_i}-{random.randint(1, 1_000_000)}",
            "type": "result",
            "transcript": transcript,
            "alts": alts,
            "alternatives": [],
            "latencyMs": 180,
            "speechLevel": 68 if st.session_state.noisy else 16,
            "startedAt": int(datetime.now(timezone.utc).timestamp() * 1000) - 900,
        }
    )


def accept_prompt() -> None:
    st.session_state.prompt_accepted = True
    log("nudge_accepted")
    if st.session_state.language_choice == "unset":
        st.session_state.screen = "language"
    else:
        st.session_state.screen = "listen"


def dismiss_prompt() -> None:
    st.session_state.prompt_dismissed = True
    log("nudge_dismissed")


def open_mic() -> None:
    if st.session_state.language_choice == "unset":
        if st.session_state.version == "A":
            st.session_state.language_choice = "en"
            st.session_state.screen = "listen"
        else:
            st.session_state.screen = "language"
        return
    st.session_state.screen = "listen"


def go(screen: str) -> None:
    st.session_state.screen = screen


def pick_language(code: str) -> None:
    st.session_state.language_choice = code
    st.session_state.screen = "listen"


def randomize_arm() -> None:
    st.session_state.version = random.choice(["A", "B"])


def send_typed() -> None:
    transcript = (st.session_state.get("draft") or "").strip()
    if not transcript:
        st.session_state.flash = text("empty")
        return
    channel = "voice" if st.session_state.draft_from_voice else "typed"
    log("send_tapped", channel=channel, chars=len(transcript))
    deliver(transcript, channel)
    st.session_state.draft = ""
    st.session_state.draft_from_voice = False
    st.session_state.screen = "chat"


def send_review() -> None:
    review = st.session_state.review or {}
    transcript = (review.get("text") or "").strip()
    if not transcript:
        st.session_state.flash = text("empty")
        return
    log("send_tapped", channel="voice", chars=len(transcript))
    deliver(transcript, "voice")
    st.session_state.review = None
    st.session_state.screen = "chat"


def discard_review() -> None:
    log("review_abandoned", reason="discard")
    st.session_state.review = None
    st.session_state.screen = "chat"


def rerecord() -> None:
    log("review_abandoned", reason="rerecord")
    st.session_state.review = None
    st.session_state.screen = "listen"


def cycle_word(index: int) -> None:
    review = st.session_state.review
    options = review["alts"][index]
    if len(options) < 2:
        return
    current = review["words"][index]
    nxt = options[(options.index(current) + 1) % len(options)] if current in options else options[0]
    review["words"][index] = nxt
    review["text"] = " ".join(review["words"])
    st.session_state.edit_all_text = review["text"]
    log("word_edited", method="cycle", index=index)


def apply_edit() -> None:
    transcript = (st.session_state.get("edit_all_text") or "").strip()
    if not transcript:
        return
    words = transcript.split()
    st.session_state.review["words"] = words
    st.session_state.review["text"] = " ".join(words)
    st.session_state.review["alts"] = [[word] for word in words]
    log("word_edited", method="edit_all")


def use_sample(question: str) -> None:
    words = question.split()
    if st.session_state.screen == "review" and st.session_state.review:
        st.session_state.review["words"] = words
        st.session_state.review["text"] = question
        st.session_state.review["alts"] = [[word] for word in words]
        st.session_state.edit_all_text = question
    else:
        open_review(question, [[word] for word in words], 0, None)
    log("sample_question_picked", question=question)


def open_test_prompt() -> None:
    if st.session_state.language_choice == "unset":
        st.session_state.language_choice = "en"
    question = st.session_state.test_prompt
    if st.session_state.version == "A":
        st.session_state.draft = question
        st.session_state.draft_from_voice = True
        st.session_state.screen = "chat"
        log("sample_question_picked", question=question)
        return
    words = question.split()
    open_review(question, [[word] for word in words], 0, None)
    log("sample_question_picked", question=question)


def answer_comfort(value: str) -> None:
    log("comfort_survey_response", value=value)
    st.session_state.comfort_open = False


def mark_d7() -> None:
    if not st.session_state.d7_marked:
        log("voice_return_d7")
        st.session_state.d7_marked = True


def simulate_next_day() -> None:
    st.session_state.streak_date = (date.today() - timedelta(days=1)).isoformat()


def request_reset() -> None:
    st.session_state.do_reset = True


def speak(answer: str) -> None:
    st.session_state.speak_payload = {"text": answer, "lang": LANGS[effective_lang()]["bcp47"], "nonce": random.random()}


def render_sidebar() -> None:
    st.sidebar.markdown("### Gear")
    st.sidebar.caption("Prototype controls. They do not exist in the product UI.")
    st.sidebar.radio("Version", ["A", "B"], horizontal=True, key="version", help="A is current voice. B is Quiet push-to-talk. The prototype opens on B.")
    st.sidebar.button("Assign a random arm", on_click=randomize_arm, use_container_width=True)
    st.sidebar.radio("Prompt", ["On open", "After a long draft"], key="prompt_timing")
    st.sidebar.selectbox(
        "Language",
        options=["unset", *LANGS.keys()],
        format_func=lambda code: "Not chosen yet" if code == "unset" else f"{LANGS[code]['label']} · {LANGS[code]['english']}",
        key="language_choice",
    )
    st.sidebar.radio("Speech", ["Real", "Demo"], horizontal=True, key="speech_mode", help="Real listens to the microphone. Demo replays a sample question and does not use the microphone.")
    st.sidebar.toggle("Noisy place", key="noisy", help="Simulates a public ambient-noise bucket. Used only for measurement.")
    st.sidebar.toggle("Earphones in", key="earphones")
    st.sidebar.toggle("Hide review text until tap", key="hide_default")
    samples = SAMPLES[effective_lang()]
    options = [sample["q"] for sample in samples]
    if st.session_state.get("test_prompt") not in options:
        st.session_state.test_prompt = options[0]
    st.sidebar.selectbox("Test prompt", options, key="test_prompt")
    st.sidebar.button("Open this prompt", on_click=open_test_prompt, use_container_width=True)
    summary = summarize(st.session_state.events)
    if summary["guardrail_pass"]:
        st.sidebar.success("Guardrails holding")
    else:
        st.sidebar.warning("Guardrail watch")
    dismiss = "n/a" if summary["dismiss_rate"] is None else f"{summary['dismiss_rate']:.0%}"
    latency = "n/a" if summary["latency_p90_ms"] is None else f"{summary['latency_p90_ms']:.0f} ms"
    send_rate = "n/a" if summary["send_completion"] is None else f"{summary['send_completion']:.0%}"
    st.sidebar.markdown(
        f"Prompt dismiss **{dismiss}** · target < 40%  \n"
        f"Latency p90 **{latency}** · target ≤ 2 s  \n"
        f"Send completion **{send_rate}** · watch if it falls  \n"
        f"Public retries **{summary['public_retries']}** of **{summary['public_attempts']}** public attempts"
    )
    st.sidebar.button("Mark a day-7 return", on_click=mark_d7, use_container_width=True)
    st.sidebar.button("Simulate the next day", on_click=simulate_next_day, use_container_width=True)
    payload = json.dumps(st.session_state.events, ensure_ascii=False, indent=2)
    st.sidebar.download_button(
        "Download events.json",
        data=payload.encode("utf-8"),
        file_name="quiet-voice-events.json",
        mime="application/json",
        use_container_width=True,
    )
    with st.sidebar.expander("Event log"):
        st.code(payload or "[]", language="json")
    st.sidebar.button("Reset everything", on_click=request_reset, use_container_width=True)


def render_header() -> None:
    language = event_language()
    subtitle = f'<div class="gpt-sub">{html.escape(LANGS[language]["label"])}</div>' if language else ""
    st.markdown(
        f'<div class="gpt-top"><div class="gpt-name">ChatGPT</div>{subtitle}</div>',
        unsafe_allow_html=True,
    )


def render_thread() -> None:
    if not st.session_state.messages:
        st.markdown(
            f'<div class="gpt-empty"><div class="gpt-mark"></div><h2>{html.escape(text("empty_title"))}</h2></div>',
            unsafe_allow_html=True,
        )
        return
    for index, message in enumerate(st.session_state.messages):
        body = html.escape(message["text"]).replace("\n", "<br>")
        if message["role"] == "user":
            st.markdown(f'<div class="gpt-user-row"><div class="gpt-user">{body}</div></div>', unsafe_allow_html=True)
            continue
        st.markdown(
            f'<div class="gpt-ai"><div class="gpt-mark sm"></div><div class="gpt-ai-body">{body}</div></div>',
            unsafe_allow_html=True,
        )
        if st.button(text("listen"), key=f"listen-{index}"):
            speak(message["text"])


def render_win() -> None:
    if not st.session_state.show_win:
        return
    st.markdown(
        f'<div class="gpt-note">{html.escape(text("worked"))} · {st.session_state.streak} {html.escape(text("streak"))}<br>{html.escape(text("worked_next"))}</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.comfort_open:
        st.caption(text("comfort"))
        awkward, okay, comfortable = st.columns(3)
        awkward.button(text("awkward"), on_click=answer_comfort, args=("awkward",), use_container_width=True)
        okay.button(text("okay"), on_click=answer_comfort, args=("okay",), use_container_width=True)
        comfortable.button(text("comfortable"), on_click=answer_comfort, args=("comfortable",), use_container_width=True)


def render_few_suggestions() -> None:
    picks = [(code, SAMPLES[code][0]) for code in ("hi", "hinglish")]
    columns = st.columns(2)
    for column, (code, sample) in zip(columns, picks):
        column.button(
            sample["q"],
            key=f"suggest-{code}",
            on_click=ask_suggestion,
            args=(code, sample["q"]),
            use_container_width=True,
        )


def render_chat() -> None:
    render_thread()
    if prompt_visible():
        st.markdown(
            f'<div class="gpt-suggest"><strong>{html.escape(text("prompt_title"))}</strong><p>{html.escape(text("prompt_body"))}</p></div>',
            unsafe_allow_html=True,
        )
        left, right = st.columns(2)
        left.button(text("tap_try"), type="primary", on_click=accept_prompt, use_container_width=True)
        right.button(text("not_now"), on_click=dismiss_prompt, use_container_width=True)
    render_win()
    field, mic = st.columns([8, 1.2])
    field.text_input("Message", key="draft", label_visibility="collapsed", placeholder=text("placeholder"))
    mic.button("🎤", help=text("mic"), on_click=open_mic, use_container_width=True)
    if (st.session_state.get("draft") or "").strip():
        st.button(text("send"), type="primary", on_click=send_typed, use_container_width=True)
    render_few_suggestions()


def render_language() -> None:
    st.markdown(f'<div class="gpt-screen-title">{html.escape(text("pick_title"))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gpt-muted">{html.escape(text("beta_note"))}</div>', unsafe_allow_html=True)
    for code, meta in LANGS.items():
        label = f"{meta['label']} · {meta['english']}" + (" · beta" if meta["beta"] else "")
        st.button(label, key=f"pick-{code}", on_click=pick_language, args=(code,), use_container_width=True)
    st.button(text("back"), on_click=go, args=("chat",))


def render_listen() -> None:
    quiet = st.session_state.version == "B"
    title = text("hold_title") if quiet else text("classic_title")
    st.markdown(f'<div class="gpt-screen-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if LANGS[effective_lang()]["beta"]:
        st.markdown(f'<div class="gpt-muted">{html.escape(text("beta_note"))}</div>', unsafe_allow_html=True)
    transcript, alts = demo_payload()
    strings = {key: text(key) for key in ("listening", "hearing", "hold_hint", "cancel_hint", "hidden_note", "buzz_note", "classic_hint", "unsupported", "no_speech", "mic")}
    event = MIC(
        mode="quiet" if quiet else "classic",
        demo=st.session_state.speech_mode == "Demo",
        transcript=transcript,
        alts=alts,
        bcp47=LANGS[effective_lang()]["bcp47"],
        noisy=st.session_state.noisy,
        strings=strings,
        epoch=st.session_state.epoch,
        key="quiet-mic",
        default=None,
    )
    st.caption(text("privacy"))
    if st.session_state.speech_mode == "Demo":
        st.button(text("demo_release"), on_click=release_demo, use_container_width=True)
    st.button(text("back"), on_click=go, args=("chat",))
    if remember(event):
        apply_mic_event(event)
        st.rerun()


def render_review() -> None:
    review = st.session_state.review
    if not review:
        st.session_state.screen = "chat"
        st.rerun()
    st.markdown(f'<div class="gpt-screen-title">{html.escape(text("review_title"))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gpt-muted">{html.escape(text("review_hint"))}</div>', unsafe_allow_html=True)
    hidden = st.checkbox(text("hide"), key="hide_text")
    if st.session_state.hide_text_prev is not None and hidden != st.session_state.hide_text_prev:
        log("hide_text_toggled", hidden=bool(hidden))
    st.session_state.hide_text_prev = hidden
    shown = " ".join(review["words"])
    review["text"] = shown
    if hidden:
        st.markdown(f'<div class="gpt-blur">{html.escape(shown)}</div>', unsafe_allow_html=True)
        st.caption(text("show"))
    else:
        st.markdown(f'<div class="gpt-transcript">{html.escape(shown)}</div>', unsafe_allow_html=True)
        fixes = [index for index, options in enumerate(review["alts"]) if len(options) > 1]
        for index in fixes:
            word = review["words"][index]
            st.button(
                f'{text("fix")}: {word}',
                key=f"fix-{index}-{word}",
                on_click=cycle_word,
                args=(index,),
            )
    st.text_area(text("edit_all"), key="edit_all_text")
    st.button(text("apply_edit"), on_click=apply_edit)
    send, again, discard = st.columns(3)
    send.button(text("send"), type="primary", on_click=send_review, use_container_width=True)
    again.button(text("rerecord"), on_click=rerecord, use_container_width=True)
    discard.button(text("discard"), on_click=discard_review, use_container_width=True)
    st.caption(text("samples"))
    for index, sample in enumerate(SAMPLES[effective_lang()]):
        st.button(sample["q"], key=f"sample-{index}", on_click=use_sample, args=(sample["q"],), use_container_width=True)


def render_speech() -> None:
    payload = st.session_state.pop("speak_payload", None)
    if not payload:
        return
    spec = json.dumps({"text": payload["text"], "lang": payload["lang"]})
    components.html(
        f"""
        <script>
          const spec = {spec};
          const utterance = new SpeechSynthesisUtterance(spec.text);
          utterance.lang = spec.lang;
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(utterance);
        </script>
        <p style="font:12px/1.4 'Segoe UI',sans-serif;color:#6b6585;margin:0;">Playing in this browser.</p>
        """,
        height=36,
    )


def main() -> None:
    init_state()
    inject_css()
    maybe_log_nudge()
    render_sidebar()
    sync_language()
    render_header()
    flash = st.session_state.pop("flash", None)
    if flash:
        st.toast(flash)
    screen = st.session_state.screen
    if screen == "language":
        render_language()
    elif screen == "listen":
        render_listen()
    elif screen == "review":
        render_review()
    else:
        render_chat()
    render_speech()


main()
