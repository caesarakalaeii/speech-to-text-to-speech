"""ONNX Runtime execution provider selection.

The target machine is a Radeon RX 9070 XT on Windows. That rules out CUDA, and
ROCm has no Windows PyTorch story we would want to put in front of a
non-technical user. What is left is:

* **CPU** -- always available, and on a modern desktop CPU it already meets the
  latency budget (see docs/adr/0005-latency-budget.md). This is the default.
* **DirectML** -- works on any DirectX 12 GPU including RDNA 4, but only if the
  user installed the `onnxruntime-directml` wheel, and it is not automatically
  faster: the recogniser's decode loop issues many tiny kernels, and per-call
  overhead can swamp the win.

So: never guess. Use whatever is installed, and let Enable-GPU.bat measure it.
"""

from __future__ import annotations

import logging
import os

import onnxruntime as ort

log = logging.getLogger(__name__)

CPU = "CPUExecutionProvider"
DML = "DmlExecutionProvider"


def available_providers() -> list[str]:
    return list(ort.get_available_providers())


def has_gpu() -> bool:
    return DML in available_providers()


def providers(use_gpu: bool) -> list[str]:
    """Provider list for an InferenceSession, always ending in CPU fallback."""
    if use_gpu and has_gpu():
        return [DML, CPU]
    return [CPU]


def session_options(threads: int | None = None) -> ort.SessionOptions:
    """Session options tuned for latency rather than throughput.

    We run one short request at a time, so intra-op parallelism is what
    matters and inter-op parallelism only adds scheduling overhead.
    """
    if threads is None or threads == 0:
        threads = default_threads()
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    opts.inter_op_num_threads = 1
    if threads > 0:
        opts.intra_op_num_threads = threads
    opts.log_severity_level = 3  # warnings and below are noise here
    return opts


def default_threads() -> int:
    """0 means 'let ONNX Runtime decide', which is right on most machines."""
    override = os.environ.get("STTS_THREADS")
    if override and override.isdigit():
        return int(override)
    return 0


def describe() -> str:
    return f"onnxruntime {ort.__version__}, providers: {', '.join(available_providers())}"
