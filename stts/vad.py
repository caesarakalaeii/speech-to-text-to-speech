"""Streaming Silero voice activity detection.

onnx-asr ships Silero, but only exposes a batch API that wants the whole
recording up front. We need the opposite: one 32 ms frame at a time, with the
recurrent state carried forward, so the endpointer can react the instant
someone stops talking.

The model contract (Silero VAD v5) is:
    input  : float32 [batch, context + hop]   context = 64, hop = 512 @ 16 kHz
    state  : float32 [2, batch, 128]          carried between frames
    sr     : int64   [1]
    output : float32 [batch, 1]               P(speech)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import onnxruntime as ort

from . import runtime

HOP = 512
CONTEXT = 64
SAMPLE_RATE = 16000


class SileroVad:
    """Frame-by-frame speech probability with carried recurrent state."""

    def __init__(self, model_path: str | Path, threads: int = 0) -> None:
        self._session = ort.InferenceSession(
            str(model_path),
            runtime.session_options(threads),
            # The VAD runs on every single frame but is tiny; a GPU round trip
            # per 32 ms frame would cost more than the model does.
            providers=[runtime.CPU],
        )
        self._sr = np.array([SAMPLE_RATE], dtype=np.int64)
        self.reset()

    def reset(self) -> None:
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros(CONTEXT, dtype=np.float32)

    def __call__(self, frame: np.ndarray) -> float:
        if frame.shape[-1] != HOP:
            raise ValueError(f"expected {HOP} samples, got {frame.shape[-1]}")
        frame = np.asarray(frame, dtype=np.float32).reshape(HOP)

        padded = np.concatenate([self._context, frame])[None, :]
        output, self._state = self._session.run(
            ["output", "stateN"],
            {"input": padded, "state": self._state, "sr": self._sr},
        )
        self._context = frame[-CONTEXT:]
        return float(output[0, 0])
