# speech-to-text-to-speech

**Your voice goes in. A different voice comes out. Nothing leaves your PC.**

This app listens to your microphone, works out what you said, and says it again
in a voice you pick. Your real voice is never transmitted — not to your stream,
not to Discord, not to a server. It is discarded the instant it has been read.

Built for streamers who want to talk to chat in real time without their voice
being identifiable.

---

## Install (Windows)

1. Download this project as a ZIP and extract it somewhere sensible
   (`C:\stts` is ideal — avoid deeply nested folders).
2. Double-click **`Install.bat`**.
3. Wait about 10 minutes. It sets up everything, including Python.
4. Open **Speech-to-Text-to-Speech** from the desktop shortcut, or run
   **`Start.bat`**.

You do not need Python, a compiler, CUDA, or administrator rights.

### Getting it into OBS or Discord

For other apps to hear the new voice, it has to look like a microphone. That
needs a free virtual audio cable driver. The app detects whether you have one
and offers to set it up — click **"Set up virtual microphone…"**.

Once installed:

| In this app | Set to |
|---|---|
| Microphone | your real mic |
| Voice goes to | **CABLE Input** |
| Also hear it on | your headphones *(optional)* |

| In OBS / Discord / browser | Set to |
|---|---|
| Microphone | **CABLE Output** |

Now every app hears only the substituted voice.

---

## How fast is it?

The request was "ideally under 50 ms". **That is not physically possible for
this kind of tool, and no model choice changes it** — you cannot say a word
before you know which word it is, and you cannot know that until the speaker
has finished saying it. An English word takes 300–400 ms to say.

What it actually does:

| Situation | What the audience hears |
|---|---|
| One short isolated phrase | **under 1 second** before the new voice starts |
| Talking continuously | **no audible gap** — the new voice is already mid-sentence when you stop |

Those are two different things, and the second one is easy to oversell. "No
gap" means the audience is never left in silence, because the app transcribes
*while you are still talking* and speaks the part of the sentence it is already
sure about. It does **not** mean your closing words arrive instantly: they are
queued behind whatever is still playing, so the tail of a long sentence can lag
your real speech by a second or more. The app shows the real figure in its
status line.

Where the sub-second number comes from, worst case, for a short phrase said in
isolation:

| Stage | Cost |
|---|---|
| Waiting to be sure you stopped | 320 ms *(configurable, 200–800 ms)* |
| Recognition | ~190 ms |
| Synthesis | ~425 ms |
| Output buffering | ~20 ms |
| **Total** | **~950 ms** |

The end-to-end test asserts this stays under one second. Full reasoning and the
caveats on each number: [ADR 5](docs/adr/0005-latency-budget.md).

If you genuinely need sub-50 ms, the only option is direct voice conversion
(RVC and similar), which changes how your voice *sounds* but keeps your accent,
rhythm, laughter and speech habits intact. That is a much weaker privacy
guarantee, which is why this project does not use it.

---

## What's under the hood

Everything runs locally on ONNX Runtime. No PyTorch, no CUDA, no ROCm, no
FFmpeg, no system packages.

| Stage | Model | Why |
|---|---|---|
| Voice detection | Silero VAD v5 | ~2 MB, decides when you started and stopped |
| Recognition | Parakeet TDT 0.6B v2 | ~190 ms per phrase, ~3× faster than Whisper base, and it emits punctuation |
| Synthesis | Kokoro-82M (fp16) | 24 English voices, 178 MB model + 28 MB voice pack, Apache-2.0 |
| Fallback | Piper | much faster, more robotic — optional, and not benchmarked here |

Stage timings, measured on an i7-11700K (slower than the Ryzen 7 7800X3D this
was built for):

```
Parakeet TDT 0.6B v2    2.4 s of speech -> 190 ms   (Whisper base: 596 ms)
Kokoro-82M fp16         2.4 s of audio  -> 425 ms   (RTF 0.18)
```

Two things to be clear about. These are **stage** timings from `stts bench`,
not end-to-end delay — `bench` runs the recogniser and synthesiser directly and
skips voice detection, endpointing, streaming and playback. And they are the
figures recorded in [ADR 3](docs/adr/0003-speech-recognition-model.md) and
[ADR 4](docs/adr/0004-speech-synthesis-model.md) when those decisions were
made; re-run `stts bench` to see what your own machine does.

On accuracy, Parakeet is chosen on its published word error rate, not on a
measurement here — in our own comparison Whisper base and Parakeet both
transcribed the test sentences verbatim.

**The GPU is not used by default.** On an AMD card on Windows, CPU is fast
enough, more reliable, and leaves the GPU free for the game you are streaming.
`Enable-GPU.bat` will try DirectML and benchmark it if you want to compare;
`Disable-GPU.bat` reverses it. Reasoning:
[ADR 2](docs/adr/0002-onnx-runtime-only.md).

---

## If something goes wrong

Run **`Report-Problem.bat`**. It writes `stts-report.txt` to your desktop with
everything needed to diagnose it.

| Problem | Fix |
|---|---|
| Chat still hears my real voice | The app is still set as your mic somewhere. Set every app to **CABLE Output**. |
| It cuts me off mid-sentence | Raise **Response delay** in the app. |
| It repeats or garbles words | Lower **Response delay**, or move the mic closer. |
| It talks when I am silent | Your mic is picking up background noise; raise `vad_threshold` in `settings.json`. |
| The new voice lags a long way behind me | Expected on long unbroken sentences — see [How fast is it?](#how-fast-is-it) Pause at clause boundaries and it catches up. |
| Nothing happens at all | Check the mic level meter moves when you speak. |

Settings, logs and models live in `%LOCALAPPDATA%\stts`.

---

## For developers

```bash
uv sync --group dev    # set up
uv run stts setup      # download the ~870 MB of models
uv run stts            # open the GUI
uv run pytest          # 65 tests
```

### With Nix

The flake covers the whole thing — running the app included, not just the tests:

```bash
nix flake check         # 57 unit tests, hermetic, exits non-zero on failure
nix run .# -- doctor    # check the environment
nix run .# -- setup     # download the ~870 MB of models
nix run .#              # open the GUI
nix develop             # same deps + pytest + uv, for hacking
```

It pins Python 3.13 to match `.python-version`. `kokoro-onnx`, `phonemizer-fork`
and `espeakng-loader` are not in nixpkgs, so the flake builds them: the first
two from their PyPI wheels, and `espeakng-loader` as a shim pointing at
nixpkgs' `espeak-ng` rather than the vendored binary in the upstream wheel.

`nix flake check` deliberately runs only the unit tests — a build sandbox has no
business downloading 870 MB. Once `setup` has run, `nix develop` then `pytest`
executes all 65.

### Running it on Linux

It works, with one gap: the virtual-microphone helper is Windows-only
(VB-CABLE). To feed OBS or Discord on Linux, make a PipeWire null sink and
select it as the output device — the app says as much if you click the button.
Everything else (capture, recognition, synthesis, monitoring) is
platform-independent. `stts devices` lists what it can see.

Other commands: `stts doctor` (environment check), `stts devices` (list audio
devices), `stts bench [--gpu]` (measure recogniser and synthesiser latency).

### Layout

```
stts/
  pipeline.py     orchestration: capture -> VAD -> recognise -> synthesise -> play
  segmenter.py    endpointing state machine (pure logic, no models)
  text.py         hallucination filter, LocalAgreement, sentence chunking
  vad.py          streaming Silero wrapper
  stt.py          Parakeet via onnx-asr
  tts.py          Kokoro, plus the router that dispatches per voice
  tts_piper.py    optional Piper fallback, voices fetched on first use
  audio/          device enumeration, capture, playback, resampling
  gui.py          Tkinter front end
  cli.py          entry point and the setup/doctor/devices/bench subcommands
  config.py       settings.json schema, defaults and clamping
  models.py       model registry and downloads
  runtime.py      ONNX Runtime provider and thread selection
  install.py      post-install: models, desktop shortcut, virtual mic check
  windows.py      VB-CABLE detection and guided install
  paths.py        app dirs + the espeak-ng path-length guard
```

`pytest` runs 57 unit tests with no models needed, plus 8 end-to-end tests that
load the real models, synthesise speech, push it through the whole pipeline and
check the words survive the round trip. The e2e tests skip themselves if the
models are not downloaded. They fake the microphone and the speaker, so their
latency assertion excludes real playback-queue wait — see `FakePlayer` in
`tests/test_pipeline_e2e.py`.

Architecture decisions, with the measurements behind them, are in
[`docs/adr/`](docs/adr/). Changing a model, the runtime, the latency strategy
or the installer needs a new one.

---

## Privacy

Everything runs locally. No telemetry, and no audio is ever written to disk —
the transcript exists only in memory and in the app window.

The app reaches the network in three places, all of them downloads and none of
them carrying your audio or text: the one-time model download, the optional
Piper voices when you first select one, and the VB-CABLE installer if you ask
it to set up the virtual microphone. Nothing is uploaded at any point.

Your real voice is never sent anywhere — but note that this masks *voice*, not
*content*. It will faithfully repeat anything identifying that you say out loud.

## Licence

**GNU AGPL-3.0** — see [LICENSE](LICENSE). Models carry their own licences:
Kokoro-82M (Apache-2.0), Parakeet TDT (CC-BY-4.0), Silero VAD (MIT), Piper
voices (MIT). VB-CABLE is third-party donationware from VB-Audio, downloaded
from them directly and not redistributed here.
