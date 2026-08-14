"""Audio playback to one or two output devices.

Two, because a streamer needs the masked voice to go into the virtual cable
(so OBS and Discord pick it up) while also hearing it themselves. Each device
gets its own stream and its own buffer, since they may run at different rates.
"""

from __future__ import annotations

import logging
import threading

import numpy as np

from .devices import Device
from .resample import resample

log = logging.getLogger(__name__)


class _Sink:
    """A single output stream fed from a growing float32 buffer."""

    def __init__(self, device: Device | None, volume: float = 1.0) -> None:
        self._device = device
        self._volume = volume
        self._buffer = np.zeros(0, dtype=np.float32)
        self._lock = threading.Lock()
        self._stream = None
        self.rate = int(device.default_samplerate) if device else 48000
        self.underruns = 0

    def start(self) -> None:
        import sounddevice as sd

        self._stream = sd.OutputStream(
            device=self._device.index if self._device else None,
            channels=1,
            samplerate=self.rate,
            blocksize=0,  # let PortAudio pick its lowest safe block size
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()
        log.info(
            "Playing to %s at %d Hz",
            self._device.name if self._device else "system default",
            self.rate,
        )

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def _callback(self, outdata, frames, time_info, status) -> None:  # noqa: ANN001
        with self._lock:
            available = min(frames, len(self._buffer))
            if available:
                outdata[:available, 0] = self._buffer[:available]
                self._buffer = self._buffer[available:]
            if available < frames:
                outdata[available:, 0] = 0.0
                if len(self._buffer) == 0 and available > 0:
                    self.underruns += 1

    def write(self, audio: np.ndarray, sample_rate: int) -> None:
        chunk = resample(audio, sample_rate, self.rate)
        if self._volume != 1.0:
            chunk = chunk * self._volume
        np.clip(chunk, -1.0, 1.0, out=chunk)
        with self._lock:
            self._buffer = np.concatenate([self._buffer, chunk])

    def clear(self) -> None:
        with self._lock:
            self._buffer = np.zeros(0, dtype=np.float32)

    @property
    def queued_s(self) -> float:
        with self._lock:
            return len(self._buffer) / self.rate


class Player:
    """Fan audio out to a primary device and an optional monitor device."""

    def __init__(
        self,
        output: Device | None,
        monitor: Device | None = None,
        volume: float = 1.0,
        monitor_volume: float = 1.0,
    ) -> None:
        self._sinks = [_Sink(output, volume)]
        if monitor is not None and (output is None or monitor.index != output.index):
            self._sinks.append(_Sink(monitor, monitor_volume))

    def start(self) -> None:
        for sink in self._sinks:
            sink.start()

    def stop(self) -> None:
        for sink in self._sinks:
            sink.stop()

    def play(self, audio: np.ndarray, sample_rate: int) -> None:
        for sink in self._sinks:
            sink.write(audio, sample_rate)

    def clear(self) -> None:
        for sink in self._sinks:
            sink.clear()

    @property
    def queued_s(self) -> float:
        """Seconds of audio still waiting on the primary output."""
        return self._sinks[0].queued_s if self._sinks else 0.0
