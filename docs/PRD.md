# Quiet Voice Mode

Helping regional-language ChatGPT mobile users move from trying voice once to using it daily, by making it comfortable to use around other people.

| | |
| --- | --- |
| Team | Next Leap · Milestone 3 |
| Contributor | Noira Khan |
| Status | Research prototype, ready to run |
| This build | Streamlit prototype in this repository |
| Product launch | Still the Week 12 rollout in the plan below. This repo does not ship inside ChatGPT. |
| Evidence | Milestone 2 survey + interviews (n = 27) |

The earlier static phone walkthrough is replaced by this prototype. Reviewers can speak, or use demo speech, in Hindi, Marathi, Bengali, Tamil, Telugu, Hinglish, and English, then export the event log.

## 1. Problem definition

This paragraph is unchanged.

Regional-language (Hindi, Hinglish and other) ChatGPT mobile users in India know about voice input — 25 of 27 surveyed (93%) have tried it — yet they report falling back to typing whenever other people are around. The blocker is social comfort, not discovery or accuracy: 52% feel awkward or self-conscious speaking to their phone in front of others, versus 33% who distrust accent recognition. This segment is roughly 22% of India’s ChatGPT base (Zebracat, 2026) and strategic for OpenAI, which is investing in Indic-language voice support and a Mumbai office (WebProNews, Feb 2026), so turning one-time triers into repeat voice users is a high-leverage engagement gain. If solved, users can speak queries in shared or public places without feeling watched or overheard, and the business gains repeat voice usage from people who already trust the feature. It is urgent because voice habits are forming now, and every uncomfortable public attempt pushes users back to typing and hardens that habit.

## 2. Goals

Increase repeat, comfortable voice-input use among regional-language users on ChatGPT mobile, especially in shared or public settings where usage drops off.

| Priority | Metric | Target | Definition used for the decision |
| --- | --- | --- | --- |
| 1 | Public-setting retry rate | +30% in 8 weeks | Share of regional-language users who send with voice, then start voice again within 7 days while `public_setting_flag` is true. The flag is on only when the ambient bucket is moderate or loud and earphones are out. |
| 2 | Comfort score | 52% → under 35% feel awkward | One-tap survey after a voice send: Awkward / Okay / Comfortable. Numerator is Awkward. |
| 3 | Voice conversion after the prompt | +25% | Sessions that start a hold after `nudge_shown`, divided by sessions where the prompt was shown. |
| 4 | 7-day voice retention | +15% vs control | First-time voice users in the arm who produce another `voice_hold_start` within 7 days. |
| 5 | Drop-off after first use | −20% | Users with exactly one voice send and no later voice hold, versus control. |
| 6 | Weekly active voice users | +25% in 3 months | Lagging. Distinct users with at least one voice send in the week. |
| Diagnostic | Transcript edit rate | No target yet | `word_edited` divided by `transcript_review_shown`. Separates recognition trouble from comfort. |

Guardrails, checked before any rollout step:

- Transcript latency p90 ≤ 2 seconds, from release of the mic to a reviewable transcript (`transcript_latency_ms`).
- Prompt dismiss rate under 40% (`nudge_dismissed` / `nudge_shown`).
- Send completion must not fall. In the product this is voice and typed sends per session versus control. In this prototype the console watches `send_tapped` / (`send_tapped` + `review_abandoned`), ignoring abandons whose reason is `rerecord`, and flags a drop under 80% in the current session.
- Quiet-speech recognition is checked in the Week 4 field test. This prototype does not claim that result.

We never trade answer quality for adoption. The prototype uses the same fixed answers in both arms so the comparison is the voice flow, not the reply.

## 3. Non-goals

- Training or tuning a speech model, including accent adaptation. Version 1 only sets the recognizer to the language the user picks. Accent distrust is the secondary signal (33%) and is watched through the edit rate.
- Whisper-tuned recognition and location-based “shared space” detection. In version 1, quiet means a quiet screen and a silent buzz, not a whisper model.
- Changing ChatGPT’s answers or models. This prototype returns fixed sample answers. A production build keeps the real response.
- A standalone assistant, a new app icon, keyboard work, or enterprise privacy tooling.
- Storing audio. The prototype keeps an event log in the session and nothing else.

## 4. Evidence

n = 27 weekly ChatGPT mobile users who type in a regional language.

| Insight | What we found | What we will not do because of it |
| --- | --- | --- |
| Awareness and trial | 93% (25/27) have tried voice. Only 1/27 never noticed the mic. | No discovery campaign and no new mic button. |
| Social discomfort | 52% feel awkward speaking to their phone around others. Strongest, most consistent signal. | This is the thing version 1 is built to change. |
| Accent trust | 33% distrust accent or language recognition. | Track it. Do not block version 1 on a new model. |
| “Typing only” mental model | 26% agree, 70% disagree. | Rejected as the driver. |
| Private success | 59% (16/27) said voice worked well. | The product already works at home. The gap is the shared setting. |

In their words: “outside, felt uncomfortable” · “public place, prefer to write” · “people around me might hear” · “didn’t want others to hear what I’m saying”.

WhatsApp voice notes already taught hold-to-record and slide-to-cancel in this market, so Quiet push-to-talk borrows that gesture. Dictation tools such as Gboard and Siri show live text while the person is speaking. That live text is the exposure this flow removes. The survey is self-reported, so the Week 4 test still has to watch real public settings before a beta.

## 5. Who it is for

Hindi, Hinglish, and other regional-language ChatGPT mobile users, about 22% of India’s ChatGPT base (Zebracat, 2026). Absolute size still needs internal data. The prototype covers Hindi, Marathi, Bengali, Tamil, Telugu, Hinglish, and English. Regional interface copy is marked beta until a native speaker reviews it.

Today: voice works at home, then the person hesitates at the mic on a bus, in class, or in an office, and types instead.

With Quiet Voice Mode: they see one prompt, pick a language, hold and speak softly, check or hide the text, send, then get an answer, a streak, and a comfort check.

What they still need: their own language rather than being pushed into English; a gesture that does not look like taking a call; confidence that nothing is readable or audible nearby before they send; a way to fix one misheard word without speaking again; a first try that is easy to refuse.

## 6. Solution

### Directions

| Direction | What it is | Impact | Effort | Confidence | Verdict |
| --- | --- | --- | --- | --- | --- |
| A. Quiet / whisper mode | A dedicated mode with a whisper-tuned mic and quiet cues | High | High | Medium–high | Deferred. Accuracy risk, and the Week 4 test has not yet shown that soft speech fails. |
| B. Context-aware prompting | Detect the moment and suggest voice | Medium | Low | Medium | The prompt is reused. Automatic place detection is not. |
| C. Quiet push-to-talk | Familiar hold-to-speak, transcript hidden while speaking, haptic instead of a chime, review before send, language prompt first | High | Medium | High | Chosen |

Direction C takes the quiet cues from A (hidden transcript, haptic, no chime) and the prompt from B. People still speak aloud. That is an accepted trade until soft-speech data says a whisper model is worth the risk.

The prompt appears when the app opens, which is the default in this prototype. The original “only after a long or slow draft” idea is still testable from the gear. It is not the default, because waiting for slow typing misses the people who never start typing the private query at all.

### Flow

Version B, Quiet push-to-talk:

1. Chat opens. One prompt: “Try voice in your language”. “Not now” hides it for the session. It is never forced, and the mic still works after a dismissal.
2. Language picker: Hindi, Marathi, Bengali, Tamil, Telugu, Hinglish, English. The interface and the recognizer follow the choice. Languages other than English are labeled beta.
3. Hold to speak. Slide up to cancel. Space hold works from a keyboard. Words stay hidden. A short vibration replaces the start/stop chime. Cancel returns to the same quiet screen, so the next try is still voice rather than a fall back to the keyboard.
4. Review opens before anything can send. Tap a misheard word to cycle the recognizer’s alternatives, or edit the whole line, or pick a sample question. “Hide text until I tap it” blurs the line for people looking at the screen. Re-record and discard are both available.
5. Send. The answer is a fixed sample matched to the closest question. Anything else gets the list of samples, not a made-up answer.
6. “Voice worked, even here”, a day streak, and a one-tap comfort check. Listen reads the answer only after a tap.

Version A, current voice, is the control:

- No first-screen prompt, no hidden transcript, no review gate, no streak, no comfort check.
- Tap to start and tap to stop. Words appear while speaking. A quiet beep marks start and stop.
- The transcript lands in the composer. The person sends it themselves.
- The answer comes from the same sample matcher.

Typing stays on the chat screen in both arms. The mic is the same control people already know; it does not become a second product.

### Logic

- Review before send is mandatory in Version B and absent in Version A.
- Word alternatives come from the browser recognizer’s n-best list when the hypotheses share a word count. Demo speech always mishears one word so the fix can be tried without a microphone.
- Sample matching is shared by both arms. Small spelling differences still hit the intended answer. Production would keep ChatGPT’s real responses and delete this matcher.
- Public-setting measurement is not a product behavior. The gear can mark a noisy place and earphones. The event stores a noise bucket, earphone status, and `public_setting_flag`. Real earphone detection and on-device noise classification are production work; the prototype simulates them so the metric can be traced.
- A second microphone stream is not opened during real speech. On Chrome it fights the speech recognizer. Demo speech logs a stand-in level (low, or high when “noisy place” is on).
- New data is an in-session event list. There is no new account schema and no audio file.
- The gear holds the controls a researcher needs: version, prompt timing, language, demo or real speech, noisy place, earphones, hide-text default, test prompts, guardrail summary, day-7 mark, event JSON, and reset.

### What changed from the previous prototype

- The prompt leads with language, and the screen copy follows that language.
- Seven languages, with fixed answers and a matcher, so a test is not stuck on one English sentence.
- Real browser speech, with demo speech as the path that always works.
- Hide-text, an event log, an A/B arm, and guardrail counts.
- Cancel stays on the whisper screen.
- Keyboard hold and a demo-release control, so the flow is usable without a perfect touch gesture.
- The slow-typing prompt is a switch, not the only behavior.

## 7. Events

Every event has `id`, `name`, `ts`, `version` (`A` or `B`), `language` (or null), and `props`.

| Name | When |
| --- | --- |
| `nudge_shown` | The prompt is actually on screen for the first time this session. |
| `nudge_accepted` | Tap to try. |
| `nudge_dismissed` | Not now. |
| `lang_picked` | The language changes to a real choice. |
| `voice_hold_start` | A hold or classic capture finishes. `ts` is when it started. Includes the noise bucket, earphones, and `public_setting_flag`. |
| `voice_cancel` | Slide up, Escape, or an equivalent cancel. |
| `transcript_review_shown` | Version B review opened. |
| `word_edited` | A word was cycled or the whole line was applied. |
| `sample_question_picked` | A sample question replaced the draft. |
| `hide_text_toggled` | The review blur was turned on or off. |
| `send_tapped` | Send, with `channel` of `voice` or `typed`. |
| `review_abandoned` | Discard, or re-record (`reason` = `rerecord`). Re-record is excluded from the send-completion guardrail. |
| `noise_bucket` | With `earphone_status` and `public_setting_flag`. |
| `speech_level` | Present when a level was measured or simulated. |
| `answer_shown` | A sample answer or the sample list was shown. |
| `voice_return_d7` | The researcher marks a return visit. The prototype cannot see a real seventh day. |
| `comfort_survey_response` | Awkward, Okay, or Comfortable. |
| `transcript_latency_ms` | Milliseconds from the start of the capture to a transcript. |

The gear can download `events.json`. Nothing is written to a server by this app.

## 8. Experiment

Four weeks, 50% Quiet push-to-talk (B) versus 50% current voice (A), regional-language mobile users. Primary metric is public-setting retry rate. Both arms must keep the guardrails above.

This prototype opens on B so a reviewer sees the new flow. “Assign a random arm” in the gear draws A or B the way the experiment would. Answers stay identical across arms.

The prototype’s public-retry count is a session illustration: a `voice_hold_start` with `public_setting_flag` after an earlier `send_tapped`. It is not the 8-week experiment result.

## 9. Privacy, accessibility, and risks

- The browser’s speech recognizer, in Chrome, sends audio to that browser’s speech service. The app stores no audio and no account. Say this on the whisper screen, which the prototype does.
- Ambient state in the prototype is a toggle. A production build may log only a coarse noise bucket, and must disclose that.
- Hide-text defaults off. The gear can default it on, which is the open test of privacy against readability.
- Hold-to-speak has a keyboard equivalent (Space to hold, Escape to cancel) and a demo-release button so a failed gesture is not a dead end.
- Regional copy and recognizers are beta. Do not treat a good demo in English as evidence that Tamil or Telugu is ready on a mid-range Android phone.
- Sample answers will look confident and wrong if someone asks a real question outside the set. The unmatched state lists the samples instead of inventing an answer. This must not be confused with ChatGPT quality.
- Streamlit session memory holds the event log until reset or timeout. Do not dictate passwords or other secrets into the prototype.

## 10. Launch plan for the product

This repository is the research prototype. The mobile rollout below is still the product plan and is not built here.

| Week | Milestone |
| --- | --- |
| 1 | PRD sign-off and prototype review |
| 2–3 | Design, copy, and native-speaker review |
| 4 | 5–8 sessions in public settings, including soft speech |
| 5 | Engineering scope: haptics, noise bucket, recognizer fallback |
| 8 | Development complete |
| 9 | Internal QA and dogfooding, including low-end Android |
| 10 | 10% beta behind a flag |
| 12 | Full rollout only if the primary metric and the guardrails hold |

Rollback if send completion falls or transcript latency p90 exceeds 2 seconds.

Before a beta, support needs a help article and a native-speaker pass on Hindi, Marathi, Bengali, Tamil, Telugu, and Hinglish. Speech needs a real-device check of quiet speech and regional recognition. Mobile needs a fallback when a phone has no vibration motor or no Listen voice for that language. Data needs the dashboard live before the beta. Privacy needs the disclosure above.

## 11. Decisions and open questions

Decisions:

- Optimize for comfort, not discovery or accuracy.
- Ship Direction C, with quiet cues from A and the prompt from B.
- Review before send is mandatory in the quiet arm. One prompt only. Haptics replace chimes in that arm only.
- Language comes first. The recognizer and the interface follow it.
- Fixed sample answers in the prototype, so the arm comparison is not an answer-quality comparison.
- The open-app prompt is the default. The slow-draft prompt remains a test arm in the gear.
- Cancel stays on the whisper screen.

Open:

- May the prompt return after “Not now”, and after how long?
- Does soft speech degrade recognition enough to pull the whisper model forward? Week 4 decides.
- Should hide-text be on by default?
- Which regional languages ship first on mid-range Android, once real-device Listen voices and recognizers are measured?

Descoped to a later version: whisper-tuned recognition, location-based shared-space detection, accent-model work, and making the slow-typing prompt the only trigger.
