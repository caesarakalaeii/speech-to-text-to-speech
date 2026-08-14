# 5. Latency budget and speculative transcription

Date: 2026-08-13

## Status

Accepted

## Context

The requested target was "ideally under 50 ms, realistically sub-1 s is
acceptable" for a live streamer talking to chat.

**50 ms is not achievable by a transcribe-then-speak architecture, and no
choice of model changes that.** The reason is structural rather than a
performance problem: you cannot synthesise a word before you know which word
it is, and you cannot know which word it is until the speaker has finished
saying it. An average English word takes 300-400 ms to say. Add the time to
recognise it, and the floor for *any* speech-to-text-to-speech system is
several hundred milliseconds, on any hardware.

The only architecture that reaches tens of milliseconds is **direct voice
conversion** -- transforming timbre frame by frame without ever recognising
words (RVC, seed-vc and similar). It was considered and rejected here, because
it does not do what this user actually wants. Voice conversion preserves
prosody, accent, cadence, disfluencies, laughter and coughs; it changes how a
voice *sounds* but keeps everything about how a person *speaks*. For someone
whose goal is that their real voice cannot leak, that is a much weaker
guarantee. Transcribing and re-speaking discards every biometric cue, which is
the entire point.

So the design target is the second one the user gave: **comfortably under one
second**, and as far under as the architecture allows.

## Decision

Four costs make up the delay, measured from the moment the user stops talking:

| Stage                        | Cost      | Notes |
|------------------------------|-----------|-------|
| Endpoint detection           | 320 ms    | configurable, 200-800 ms |
| Recognition                  | ~190 ms   | Parakeet, i7-11700K, ADR 3 |
| Synthesis                    | ~425 ms   | Kokoro fp16, one sentence, ADR 4 |
| Output buffering             | ~20 ms    | PortAudio, estimated not measured |
| **Naive total**              | **~950 ms** | just inside the budget |

That total is the worst case: a short phrase said in isolation, where nothing
can be overlapped. Three decisions pull the typical figure below it, and remove
the audible gap entirely for continuous speech.

**1. Speculative transcription while the user is still speaking.** Every
400 ms the recogniser runs on the audio so far. Each pass costs ~190 ms and
happens during speech, so it is free in wall-clock terms.

**2. Commit only what two consecutive passes agree on** (LocalAgreement-2,
`stts.text.LocalAgreement`). A growing transcript is volatile at the tail
-- the recogniser revises the last word or two once it hears more context, so
"welcome to the stripe" becomes "welcome to the stream". Speaking the tail
immediately would speak words the user never said. Speaking only the agreed
prefix is safe, and that prefix is available long before the sentence ends.

**3. Synthesise in sentence-sized chunks** so playback of one chunk overlaps
generation of the next (`stts.text.SpeechBuffer`). A speaker who never
pauses still gets audio, because the buffer releases at a clause boundary once
it passes 140 characters.

Together these mean that for continuous speech, audio is *already playing* when
the speaker stops, so the audience is never left in silence.

**That is continuity, not zero latency, and the two must not be conflated.**
An earlier revision of this ADR and of the README claimed a measured "0 ms"
response for continuous speech. That number was not a measurement. The pipeline
literally recorded the constant `0.0` whenever the output queue was non-empty:

```python
already_audible = self._player.queued_s > 0.02
...
self.stats.record_response(
    0.0 if already_audible else time.perf_counter() - chunk.ended_at
)
```

Two things were wrong with it. It reported zero for the case that has the
*most* latency, since a chunk queued behind 800 ms of unplayed audio waits that
800 ms before anyone hears it. And no test ever exercised the branch: the e2e
suite's `FakePlayer.queued_s` is hardcoded to `0.0`, so `already_audible` was
always false there and the constant was never reached under test.

`Pipeline._tts_loop` now records `elapsed + queued_ahead_s` — the real time
from the speaker falling silent to that chunk becoming audible — and counts the
gapless case separately in `Stats.gapless`. The GUI status line therefore shows
a true delay figure rather than a flattering zero.

Streaming can be turned off (`streaming: false`), which costs about half a
second of delay and some CPU.

## Consequences

- The honest claim is: **worst case under one second for a short isolated
  phrase, and no audible gap during continuous speech** -- with the tail of a
  long unbroken sentence lagging further behind, bounded by the output queue.
  Not 50 ms, and not zero, and the README says so rather than implying
  otherwise.
- What is actually asserted in CI is the sub-second bound
  (`test_response_latency_is_under_one_second`). Because the fake player
  swallows audio instantly, that assertion covers recognise + synthesise but
  excludes playback-queue wait, so treat it as a floor on real-world response
  latency rather than an estimate of it. Measuring the real figure needs a real
  device; `Stats.response_ms` in the running app is the number to trust.
- `endpoint_ms` is the dial that matters and it is exposed in the GUI. Below
  ~250 ms it starts cutting people off mid-sentence.
- Speculative passes cost CPU proportional to utterance length: a 10-second
  utterance re-transcribes 10 seconds every 400 ms. `Pipeline._next_segment`
  discards stale partials so the recogniser can never fall behind
  unboundedly, and `max_utterance_ms` caps the growth.
- Committed text is spoken and cannot be recalled. If the recogniser revises a
  word after we committed it, the revision is dropped rather than repeated --
  saying it twice would be worse than saying it slightly wrong.
