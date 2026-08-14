"""Microphone capture, delivered as fixed-size 16 kHz frames."""

from __future__ import annotations

import logging
import queue
import threading

import numpy as np

from ..vad import HOP, SAMPLE_RATE
from .devices import Device
from .resample import resample, to_mono

log = logging.getLogger(__name__)


class MicCapture:
    """Opens an input stream and emits exact `HOP`-sample frames at 16 kHz.

    The device is opened at its own preferred sample rate rather than forced to
    16 kHz: on Windows, shared-mode WASAPI will happily accept a rate it then
    does not honour. We resample and re-block ourselves, which also means any
    device rate works, including 44.1 kHz where the ratio is not an integer.
    """

    def __init__(self, device: Device | None, gain: float = 1.0) -> None:
        self._device = device
        self._gain = gain
        self._frames: queue.Queue[np.ndarray] = queue.Queue(maxsize=256)
        self._carry = np.zeros(0, dtype=np.float32)
        self._stream = None
        self._lock = threading.Lock()
        self.overflows = 0
        self.device_rate = int(device.default_samplerate) if device else SAMPLE_RATE

    def start(self) -> None:
        import sounddevice as sd

        # ~32 ms of device audio per callback keeps latency low without
        # waking the callback so often that Python cannot keep up.
        blocksize = max(HOP, int(self.device_rate * 0.032))
        self._stream = sd.InputStream(
            device=self._device.index if self._device else None,
            channels=1,
            samplerate=self.device_rate,
            blocksize=blocksize,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()
        log.info(
            "Capturing from %s at %d Hz",
            self._device.name if self._device else "system default",
            self.device_rate,
        )

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            # Input overflow means we lost samples; worth surfacing, not fatal.
            self.overflows += 1
        block = to_mono(np.asarray(indata, dtype=np.float32))
        if self._gain != 1.0:
            block = block * self._gain
        block = resample(block, self.device_rate, SAMPLE_RATE)

        with self._lock:
            self._carry = np.concatenate([self._carry, block])
            count = len(self._carry) // HOP
            if count:
                usable, self._carry = (
                    self._carry[: count * HOP],
                    self._carry[count * HOP :],
                )
            else:
                usable = None

        if usable is None:
            return
        for frame in usable.reshape(count, HOP):
            try:
                self._frames.put_nowait(frame)
            except queue.Full:
                self.overflows += 1

    def read(self, timeout: float = 0.1) -> np.ndarray | None:
        try:
            return self._frames.get(timeout=timeout)
        except queue.Empty:
            return None
