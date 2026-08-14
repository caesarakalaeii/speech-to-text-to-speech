# 4. Kokoro-82M (fp16) for speech synthesis

Date: 2026-08-13

## Status

Accepted

## Context

The synthesiser is what the audience actually hears, and it is the slowest
stage in the pipeline. It also has to satisfy a product requirement: the user
must be able to **pick a voice from a dropdown**, which means many voices
have to be available without a download per voice.

v1 offered four synthesisers. Two (NeuTTS Air, StyleTTS2) require PyTorch and
were far too slow. One (Speaker.bot) is an external Windows application over a
websocket, so the pipeline depended on a second program being installed,
running and configured. One (Piper) was fine but robotic.

Candidates for an ONNX-only stack:

- **Piper** -- extremely fast, one small model per voice, noticeably synthetic.
- **Kokoro-82M** -- Apache-2.0, 54 voices in a single 28 MB pack, widely
  considered the best quality per compute in its class.
- **Supertonic** -- claims 2-3x Kokoro's speed, but ships four voices and the
  model weights are OpenRAIL-M rather than a permissive licence.

## Decision

**Kokoro-82M, fp16 ONNX**, via `kokoro-onnx`, CPU by default.

Precision was measured rather than assumed. On an i7-11700K, synthesising
"Hey chat, welcome back to the stream." (2.4 s of audio) and a 105-character
sentence (6.1 s of audio):

| Weights | Size    | Threads | Short   | RTF   | Long     | RTF   |
|---------|---------|---------|---------|-------|----------|-------|
| fp32    | 326 MB  | auto    |  486 ms | 0.202 |  1283 ms | 0.209 |
| fp32    | 326 MB  | 8       |  462 ms | 0.192 |  1161 ms | 0.189 |
| **fp16**| **178 MB** | **auto** | **425 ms** | **0.184** | **1157 ms** | **0.183** |
| fp16    | 178 MB  | 8       |  413 ms | 0.179 |  1094 ms | 0.173 |
| int8    | 92 MB   | 8       | 2606 ms | 1.072 |  6002 ms | 0.994 |

fp16 is the best of both: ~8% faster than fp32 at **half the download**.

**int8 is six times slower than fp16 and slower than real time** -- it would
have made the app unusable. ONNX Runtime inserts dequantise nodes it cannot
fuse for this graph. The "obvious" optimisation was the trap; this is why the
number is in the table.

Thread count is left at ONNX Runtime's default. Forcing 4 or 16 threads was
consistently worse than the runtime's own physical-core detection.

Supertonic was rejected on voice count (four is not a dropdown) and licence.
Piper is kept as a fast, lower-quality fallback.

## Consequences

- 54 voices, of which 24 are English, selectable instantly with no extra
  download. The GUI orders them by Kokoro's published quality grade rather
  than alphabetically, so the good ones are at the top.
- Output is 24 kHz mono, resampled to whatever the output device wants.
- `kokoro-onnx` phonemises through espeak-ng, which brings the path-length
  problem documented in `stts/paths.py` and ADR 6.
- RTF ~0.18 holds on this machine and cannot be assumed elsewhere: a Ryzen 7
  PRO 5850U laptop measures ~1.75, i.e. slower than real time, which breaks the
  overlap ADR 5 depends on. Per-machine numbers:
  [BENCHMARKS.md](../BENCHMARKS.md).
- RTF ~0.18 means synthesis is the dominant cost in the pipeline. Splitting
  text into sentence-sized chunks so playback overlaps generation (ADR 5) is
  what keeps that off the critical path.
