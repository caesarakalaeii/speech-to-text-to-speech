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
nix develop       # python 3.13 + every dep + pytest + uv; then: pytest
nix run .#        # the GUI, after `nix run .# -- setup`
```

`nix flake check` is a real gate — it exits non-zero on a failing test. It runs
the unit tests only, because a build sandbox should not download 870 MB of
models; run `pytest` inside `nix develop` after `setup` to get all 65.

`kokoro-onnx`, `phonemizer-fork` and `espeakng-loader` are not in nixpkgs, so
the flake builds them. `espeakng-loader` is a shim over nixpkgs' `espeak-ng`
instead of the vendored library in the upstream wheel — if you bump it, keep
`get_library_path()` and `get_data_path()` as the only API, since that is all
`stts.tts` calls.

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
- **Record what you measure.** New timings go in
  [docs/BENCHMARKS.md](docs/BENCHMARKS.md) with the CPU, the onnxruntime source
  and version, and the execution provider. Performance here varies by more than
  an order of magnitude between machines, so a number without its context is
  not usable by anyone else.
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
