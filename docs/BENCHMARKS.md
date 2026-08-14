# Benchmarks

Measured latency per machine. This file grows as machines are added; the ADRs
record the decisions, this records the numbers.

**Every row must say who measured it and on what.** A figure without its
hardware, its onnxruntime build and its provider is not reproducible, and this
project has already been burnt once by a latency number nobody could reproduce
(see [ADR 5](adr/0005-latency-budget.md)).

## How to add a row

```bash
nix run .# -- bench          # or: uv run stts bench
nix run .# -- doctor         # for the onnxruntime version and provider list
```

Record: CPU model, whether it has AVX-512, OS, onnxruntime **source** (nixpkgs
build or PyPI wheel) and version, the active execution provider, and the
summary line. `bench` measures the recogniser and synthesiser **in isolation**
— it does not include voice detection, endpointing, streaming or playback.

## Stage timings

Kokoro-82M fp16 and Parakeet TDT 0.6B v2, CPU execution provider, ONNX Runtime
left to pick its own thread count (`STTS_THREADS` unset → `intra_op` default).

| Machine | AVX-512 | onnxruntime | Recognise (mean) | Synthesise (mean) | Kokoro RTF | Real-time capable | Source |
|---|---|---|---|---|---|---|---|
| Intel i7-11700K, desktop | yes | not recorded | 190 ms | 425 ms | 0.18 | yes | ADR 3 / ADR 4, at decision time — not reproduced since |
| AMD Ryzen 7 PRO 5850U, laptop (15–28 W) | no | nixpkgs 1.27.1 | 1573 ms | 4784 ms | 1.54–2.07 | **no** | this repo, 2026-08-14, NixOS |

RTF (real-time factor) is synthesis time ÷ audio duration. **Above 1.0 the
synthesiser is slower than speech**, so the pipeline can never catch up and the
streaming design in ADR 5 does not hold. Compare machines on RTF rather than on
absolute milliseconds: the two rows used different sentence lengths.

### Per-sentence detail

**AMD Ryzen 7 PRO 5850U** — `nix run .# -- bench`, 2026-08-14:

| Audio | Synthesise | Recognise | RTF |
|---|---|---|---|
| 2.1 s | 4350 ms | 1312 ms | 2.07 |
| 2.7 s | 4758 ms | 1830 ms | 1.76 |
| 3.4 s | 5245 ms | 1577 ms | 1.54 |
| **aggregate** | **4784 ms** | **1573 ms** | **1.75** |

Also emitted, not yet investigated:
`WARNING phonemizer: words count mismatch on 200.0% of the lines (2/1)`.

**Intel i7-11700K** — from ADR 3 and ADR 4, transcribing Kokoro-rendered speech:

| Audio | Parakeet v2 | Parakeet v2 int8 | Whisper base |
|---|---|---|---|
| 2.4 s | 190 ms | 181 ms | 596 ms |
| 2.9 s | 190 ms | 202 ms | 623 ms |
| 6.1 s | 248 ms | 260 ms | 591 ms |

## End-to-end pipeline response

From `test_response_latency_is_under_one_second`, which measures
`Stats.response_ms`: the time from the speaker falling silent to the closing
chunk becoming audible. The fake player swallows audio instantly, so this
excludes real playback-queue wait and is a **floor**, not an estimate.

| Machine | response_ms | stt_ms | tts_ms | e2e test |
|---|---|---|---|---|
| Intel i7-11700K | not measured | — | — | claimed to pass |
| AMD Ryzen 7 PRO 5850U | 4240 ms | 1264 ms | 4238 ms | **fails** (asserts < 1000 ms) |

The assertion is an absolute millisecond threshold, so it encodes one machine's
performance as a correctness condition and fails on anything slower. Worth
making relative to measured stage timings, or gating it behind a marker.

## Precision variants

Kokoro-82M, i7-11700K, from [ADR 4](adr/0004-speech-synthesis-model.md). Kept
here because int8 being *slower* is the counter-intuitive result most likely to
be re-attempted.

| Weights | Size | Threads | Short (2.4 s) | RTF | Long (6.1 s) | RTF |
|---|---|---|---|---|---|---|
| fp32 | 326 MB | auto | 486 ms | 0.202 | 1283 ms | 0.209 |
| fp32 | 326 MB | 8 | 462 ms | 0.192 | 1161 ms | 0.189 |
| **fp16** | **178 MB** | **auto** | **425 ms** | **0.184** | **1157 ms** | **0.183** |
| fp16 | 178 MB | 8 | 413 ms | 0.179 | 1094 ms | 0.173 |
| int8 | 92 MB | 8 | 2606 ms | 1.072 | 6002 ms | 0.994 |

## Open questions

- **Is the 5850U gap hardware or the onnxruntime build?** An 11× synthesis gap
  is more than a mobile part should account for on its own. Two untested
  candidates: Rocket Lake has AVX-512, which MLAS kernels exploit heavily,
  while Zen 3 has only AVX2; and the nixpkgs onnxruntime may be configured
  differently from the PyPI wheel (it also advertises
  `OpenVINOExecutionProvider`, which the wheel does not). Resolving it means
  running `bench` against the PyPI wheel on the same machine.
- **The i7-11700K row has never been reproduced**, and its onnxruntime version
  was not recorded. Treat it as provenance-weak until someone re-runs it.
- **No DirectML numbers.** `Enable-GPU.bat` benchmarks it but nobody has
  recorded the result on the target Radeon RX 9070 XT.
