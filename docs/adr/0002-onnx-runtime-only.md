# 2. ONNX Runtime is the only inference stack

Date: 2026-08-13

## Status

Accepted

## Context

The target user runs **Windows** on a **Radeon RX 9070 XT (RDNA 4)** with a
Ryzen 7 7800X3D and 32 GB of RAM. They are not technical, and the install has
to be close to a single click.

That hardware combination eliminates most of the usual options:

- **CUDA** is not available. Nothing NVIDIA-specific can be used.
- **ROCm** officially supports the RX 9070 XT as of ROCm 7.2, and AMD now
  publishes Windows PyTorch wheels (`torch 2.9.1+rocm7.2.1`, Python 3.12
  only, from `repo.radeon.com`). But it is a young, driver-version-coupled
  path: it pins a specific Adrenalin driver, pins one Python version, and a
  mismatch produces errors a non-technical user cannot act on. Betting a
  one-click installer on it is not defensible.
- **PyTorch on CPU** would work, but a torch wheel is ~2 GB and drags in a
  toolchain the user has no other use for.

v1 required PyTorch, CUDA, FFmpeg and a system-wide espeak-ng install, then
told the user to install them by hand across three tutorial documents. Two of
its four TTS backends could not run on this machine.

## Decision

Every model runs on **ONNX Runtime**. No PyTorch, no CUDA, no ROCm, no FFmpeg,
no system packages.

This is possible because ONNX builds exist for everything we need:

| Stage        | Model                          | Package    |
|--------------|--------------------------------|------------|
| Voice detect | Silero VAD v5                  | `onnx-asr` |
| Recognise    | Parakeet TDT 0.6B v2           | `onnx-asr` |
| Synthesise   | Kokoro-82M fp16                | `kokoro-onnx` |

The whole dependency set is `numpy`, `scipy`, `sounddevice`, `onnxruntime`,
`onnx-asr` and `kokoro-onnx` -- around 120 MB of wheels, all with Windows
binaries, none needing a compiler.

**CPU is the default execution provider.** GPU acceleration is offered through
**DirectML**, which works on any DirectX 12 GPU including RDNA 4 and sidesteps
ROCm entirely, but it is opt-in via `Enable-GPU.bat` and only kept if the
bundled benchmark shows it is actually faster. It usually is not for this
workload: the recogniser's transducer decode loop issues many tiny kernels, and
per-dispatch overhead can exceed the compute saved.

## Consequences

- Install is `uv sync` plus a model download. No admin rights, no reboot, no
  driver version to match.
- The GPU sits idle by default. On this hardware that is fine -- see ADR 5 for
  the measured budget -- and it leaves the GPU free for the games being
  streamed, which matters more here than shaving 100 ms.
- `onnxruntime-directml` and `onnxruntime` are separate wheels that provide the
  same import name, so enabling GPU support swaps one for the other rather than
  installing alongside. `Disable-GPU.bat` reverses it.
- We are limited to models with usable ONNX exports. That excluded several
  otherwise attractive synthesisers (Chatterbox, F5-TTS, XTTS), all of which
  are far too slow for real time on this hardware anyway.
