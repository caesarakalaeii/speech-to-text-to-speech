"""Sample rate conversion between device rates and model rates.

Devices run at 44.1 or 48 kHz; the recogniser wants 16 kHz and the synthesiser
emits 24 kHz. Doing the conversion ourselves rather than asking PortAudio to
is deliberate -- the Windows WASAPI backend only resamples in some modes, and
silently opening a stream at the wrong rate produces chipmunk audio that is
very confusing to debug.
"""

from __future__ import annotations

from math import gcd

import numpy as np
from scipy.signal import resample_poly


def resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    if from_rate == to_rate or audio.size == 0:
        return np.asarray(audio, dtype=np.float32)
    divisor = gcd(int(from_rate), int(to_rate))
    up = int(to_rate) // divisor
    down = int(from_rate) // divisor
    out = resample_poly(np.asarray(audio, dtype=np.float32), up, down)
    return np.asarray(out, dtype=np.float32)


def to_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return np.asarray(audio, dtype=np.float32)
    return np.asarray(audio, dtype=np.float32).mean(axis=1)
