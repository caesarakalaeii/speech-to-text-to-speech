# Contributing

## Setup

```bash
uv sync --group dev
uv run stts setup   # downloads ~870 MB of models, needed for the e2e tests
uv run pytest
```

### Or with Nix

```bash
nix flake check   # 57 unit tests, hermetic; e2e skip
nix develop       # shell with python 3.13 + deps + uv; then: pytest
```

`nix flake check` is a real gate — it exits non-zero on a failing test. It runs
the unit tests only, because `kokoro-onnx` and `espeakng-loader` are not
packaged in nixpkgs and the e2e tests need the downloaded models regardless.
Reach for `uv` inside `nix develop` when you need the synthesiser.

## Ground rules

- **Measure before choosing.** Every model and precision in this project was
  picked from a benchmark, not a blog post. int8 quantisation looked like an
  obvious win and turned out to be 6x slower — see
  [ADR 4](docs/adr/0004-speech-synthesis-model.md).
- **A metric must measure something.** Never substitute a constant for a
  timing, and never quote a number in the docs that no test or benchmark
  produces. The latency stat used to report a hardcoded `0.0` for the
  best-looking case, and both the README and an ADR repeated it as if it had
  been measured — see [ADR 5](docs/adr/0005-latency-budget.md). Say which tool
  produced a figure and on what hardware, or leave it out.
- **Architectural changes need an ADR.** Swapping a model, the inference
  runtime, the latency strategy or the installer means a new file in
  `docs/adr/`. Tuning a default or adding a voice does not.
- **Tests first.** The endpointer, the agreement policy and the sentence
  chunker are deliberately pure functions so they can be tested without
  loading a model. Keep them that way.
- **The user is not technical.** Anything that would make them read an error
  message, edit a config file or install a toolchain is a bug.

## Test layers

| File | Tests | Needs models | What it covers |
|---|---|---|---|
| `test_text.py` | 40 | no | hallucination filter, LocalAgreement, chunking, voices |
| `test_segmenter.py` | 17 | no | endpointing, pre-roll, max length, partials |
| `test_pipeline_e2e.py` | 8 | yes | full pipeline with real models and fake devices |

65 in total. The end-to-end tests synthesise their own input speech, push it
through the real pipeline, and assert the words survive. They skip
automatically if the models are not present.

They fake the microphone and the speaker, which bounds what their latency
assertion is worth: `FakePlayer` swallows audio instantly, so no
playback-queue wait is included. Do not quote its figure as an end-to-end
latency measurement.
