# 3. Parakeet TDT 0.6B v2 for speech recognition

Date: 2026-08-13

## Status

Accepted

## Context

The recogniser sits in the middle of the latency budget, and its errors are
not recoverable: a misheard word is spoken aloud, in a confident synthetic
voice, to the user's chat. Accuracy and speed both matter, and the user speaks
English only.

v1 defaulted to OpenAI Whisper `base` through the reference PyTorch
implementation, with NVIDIA NeMo Parakeet as an alternative that pulled in the
entire NeMo toolkit.

Candidates evaluated for an ONNX-only stack (ADR 2):

- **Whisper** (`base`/`small`), via `onnx-asr`. Whisper pads every input to 30
  seconds, so a 2-second phrase costs the same as a 30-second one -- exactly
  the wrong shape for short conversational turns.
- **Parakeet TDT 0.6B v2/v3**, via `onnx-asr`. v2 is English-only; v3 is
  multilingual with slightly worse English word error rate.
- **Moonshine v2**, whose streaming encoder is purpose-built for this and
  reports 148 ms on an M3. Its `moonshine-voice` package publishes wheels for
  macOS and Linux only -- **no Windows wheels** -- which rules it out for the
  target machine.

## Decision

**Parakeet TDT 0.6B v2**, English, fp32, on CPU, via `onnx-asr`.

Measured on an i7-11700K (slower than the target machine), transcribing
Kokoro-rendered speech:

| Model                  | 2.4 s audio | 2.9 s audio | 6.1 s audio | Transcript |
|------------------------|-------------|-------------|-------------|------------|
| Parakeet TDT 0.6B v2   | **190 ms**  | **190 ms**  | **248 ms**  | verbatim, punctuated |
| Parakeet v2 int8       | 181 ms      | 202 ms      | 260 ms      | verbatim |
| Whisper base           | 596 ms      | 623 ms      | 591 ms      | verbatim |

Parakeet is roughly 3x faster than Whisper base at better accuracy, and it
emits punctuation and casing, which the synthesiser needs to produce correct
prosody -- a sentence without a question mark is spoken with the wrong
intonation.

int8 quantisation was measured and **rejected**: it is not meaningfully faster
and costs accuracy headroom for a saving that only matters on disk.

## Consequences

- English only. Switching to `nemo-parakeet-tdt-0.6b-v3` in
  `models.STT_MODEL` gets 25 languages at a small English accuracy cost, if
  that is ever wanted.
- ~660 MB one-time download, cached by `huggingface_hub`.
- The model is non-streaming: it transcribes a complete buffer. We get
  streaming behaviour by re-running it on a growing buffer and reconciling the
  results (ADR 5), which is affordable precisely because a pass is ~200 ms.
- Recognition happens on audio at 16 kHz mono; the capture path resamples to
  that regardless of what the device runs at.
