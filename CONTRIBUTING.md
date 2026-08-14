# Contributing

## Setup

```bash
uv sync --group dev
uv run voicemask setup   # downloads ~870 MB of models, needed for the e2e tests
uv run pytest
```

## Ground rules

- **Measure before choosing.** Every model and precision in this project was
  picked from a benchmark, not a blog post. int8 quantisation looked like an
  obvious win and turned out to be 6x slower — see
  [ADR 4](docs/adr/0004-speech-synthesis-model.md).
- **Architectural changes need an ADR.** Swapping a model, the inference
  runtime, the latency strategy or the installer means a new file in
  `docs/adr/`. Tuning a default or adding a voice does not.
- **Tests first.** The endpointer, the agreement policy and the sentence
  chunker are deliberately pure functions so they can be tested without
  loading a model. Keep them that way.
- **The user is not technical.** Anything that would make them read an error
  message, edit a config file or install a toolchain is a bug.

## Test layers

| File | Needs models | What it covers |
|---|---|---|
| `test_text.py` | no | hallucination filter, LocalAgreement, chunking, voices |
| `test_segmenter.py` | no | endpointing, pre-roll, max length, partials |
| `test_pipeline_e2e.py` | yes | full pipeline with real models and fake devices |

The end-to-end tests synthesise their own input speech, push it through the
real pipeline, and assert the words survive. They skip automatically if the
models are not present.
