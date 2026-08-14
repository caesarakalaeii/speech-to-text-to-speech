# VoiceMask

**Your voice goes in. A different voice comes out. Nothing leaves your PC.**

VoiceMask listens to your microphone, works out what you said, and says it
again in a voice you pick. Your real voice is never transmitted — not to your
stream, not to Discord, not to a server. It is discarded the instant it has
been read.

Built for streamers who want to talk to chat in real time without their voice
being identifiable.

---

## Install (Windows)

1. Download this project as a ZIP and extract it somewhere sensible
   (`C:\VoiceMask` is ideal — avoid deeply nested folders).
2. Double-click **`Install.bat`**.
3. Wait about 10 minutes. It sets up everything, including Python.
4. Open **VoiceMask** from the desktop shortcut.

You do not need Python, a compiler, CUDA, or administrator rights.

### Getting it into OBS or Discord

For other apps to hear the new voice, it has to look like a microphone. That
needs a free virtual audio cable driver. VoiceMask detects whether you have one
and offers to set it up — click **"Set up virtual microphone…"** in the app.

Once installed:

| In VoiceMask | Set to |
|---|---|
| Microphone | your real mic |
| Voice goes to | **CABLE Input** |
| Also hear it on | your headphones *(optional)* |

| In OBS / Discord / browser | Set to |
|---|---|
| Microphone | **CABLE Output** |

Now every app hears only the masked voice.

---

## How fast is it?

The request was "ideally under 50 ms". **That is not physically possible for
this kind of tool, and no model choice changes it** — you cannot say a word
before you know which word it is, and you cannot know that until the speaker
has finished saying it. An English word takes 300–400 ms to say.

What VoiceMask actually does, measured end to end on hardware *slower* than the
target machine:

| Situation | Delay before chat hears you |
|---|---|
| Talking continuously | **~0 ms** — the new voice is already speaking when you stop |
| One short isolated phrase | **under 1 second** |

It gets there by transcribing *while you are still talking* and speaking the
part of the sentence it is already sure about. Details and measurements:
[ADR 5](docs/adr/0005-latency-budget.md).

If you genuinely need sub-50 ms, the only option is direct voice conversion
(RVC and similar), which changes how your voice *sounds* but keeps your accent,
rhythm, laughter and speech habits intact. That is a much weaker privacy
guarantee, which is why VoiceMask does not use it.

---

## What's under the hood

Everything runs locally on ONNX Runtime. No PyTorch, no CUDA, no ROCm, no
FFmpeg, no system packages.

| Stage | Model | Why |
|---|---|---|
| Voice detection | Silero VAD v5 | 2 MB, decides when you started and stopped |
| Recognition | Parakeet TDT 0.6B v2 | ~190 ms per phrase, 3× faster and more accurate than Whisper base |
| Synthesis | Kokoro-82M (fp16) | 24 English voices in one 178 MB file, Apache-2.0 |
| Fallback | Piper | ~10× faster, more robotic — optional |

Measured on an i7-11700K, which is slower than the Ryzen 7 7800X3D this was
built for:

```
Parakeet TDT 0.6B v2    2.4 s of speech -> 190 ms   (Whisper base: 596 ms)
Kokoro-82M fp16         2.4 s of audio  -> 425 ms   (RTF 0.18)
```

**The GPU is not used by default.** On an AMD card on Windows, CPU is fast
enough, more reliable, and leaves the GPU free for the game you are streaming.
`Enable-GPU.bat` will try DirectML and benchmark it if you want to compare;
`Disable-GPU.bat` reverses it. Reasoning:
[ADR 2](docs/adr/0002-onnx-runtime-only.md).

---

## If something goes wrong

Run **`Report-Problem.bat`**. It writes `voicemask-report.txt` to your desktop
with everything needed to diagnose it.

| Problem | Fix |
|---|---|
| Chat still hears my real voice | The app is still set as your mic somewhere. Set every app to **CABLE Output**. |
| It cuts me off mid-sentence | Raise **Response delay** in the app. |
| It repeats or garbles words | Lower **Response delay**, or move the mic closer. |
| It talks when I am silent | Your mic is picking up background noise; raise the mic threshold in `settings.json`. |
| Nothing happens at all | Check the mic level meter moves when you speak. |

Settings, logs and models live in `%LOCALAPPDATA%\VoiceMask`.

---

## For developers

```bash
uv sync --group dev        # set up
uv run voicemask setup     # download the ~870 MB of models
uv run voicemask           # open the GUI
uv run pytest              # 60 tests
```

Other commands: `voicemask doctor` (environment check), `voicemask devices`
(list audio devices), `voicemask bench [--gpu]` (measure latency).

### Layout

```
voicemask/
  pipeline.py     orchestration: capture -> VAD -> recognise -> synthesise -> play
  segmenter.py    endpointing state machine (pure logic, no models)
  text.py         hallucination filter, LocalAgreement, sentence chunking
  vad.py          streaming Silero wrapper
  stt.py          Parakeet via onnx-asr
  tts.py          Kokoro, plus the router that dispatches per voice
  audio/          device enumeration, capture, playback, resampling
  gui.py          Tkinter front end
  paths.py        app dirs + the espeak-ng path-length guard
```

`pytest` runs 52 unit tests with no models needed, plus 8 end-to-end tests that
load the real models, synthesise speech, push it through the whole pipeline and
check the words survive the round trip. The e2e tests skip themselves if the
models are not downloaded.

Architecture decisions, with the measurements behind them, are in
[`docs/adr/`](docs/adr/). Changing a model, the runtime, the latency strategy
or the installer needs a new one.

---

## Privacy

Everything is local. There is no network traffic after the one-time model
download, no telemetry, and no audio written to disk. The transcript exists
only in memory and in the app window.

Your real voice is never sent anywhere — but note that VoiceMask masks *voice*,
not *content*. It will faithfully repeat anything identifying that you say out
loud.

## Licence

MIT — see [LICENSE](LICENSE). Models carry their own licences: Kokoro-82M
(Apache-2.0), Parakeet TDT (CC-BY-4.0), Silero VAD (MIT), Piper voices (MIT).
VB-CABLE is third-party donationware from VB-Audio, downloaded from them
directly and not redistributed here.
