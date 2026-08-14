"""Turn a continuous microphone stream into utterances.

The state machine is deliberately separate from the VAD model: it consumes a
speech probability per frame and knows nothing about ONNX. That keeps the
latency-critical timing rules testable with synthetic input.

Timing terms used below, all measured in frames of `frame_ms` milliseconds:

* **pre-roll** -- audio kept from *before* speech was detected. Without it the
  first consonant is clipped, and the recogniser guesses the wrong word.
* **endpoint** -- how much trailing silence ends an utterance. This is the
  single biggest contributor to end-to-end latency, so it is tunable.
* **max utterance** -- a hard cap so someone who never pauses still gets
  their speech through.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class SpeechStarted:
    at: float


@dataclass(frozen=True)
class Partial:
    """Audio so far, emitted mid-utterance so we can transcribe speculatively."""

    audio: np.ndarray
    at: float


@dataclass(frozen=True)
class Utterance:
    audio: np.ndarray
    at: float
    reason: str  # "endpoint" | "max_length"


Event = SpeechStarted | Partial | Utterance


@dataclass
class EndpointerConfig:
    sample_rate: int = 16000
    frame_samples: int = 512  # Silero VAD's native frame size at 16 kHz
    threshold: float = 0.5
    # Hysteresis: entering speech is deliberately eager, leaving it is not.
    start_ms: int = 64
    endpoint_ms: int = 320
    min_speech_ms: int = 200
    max_utterance_ms: int = 12000
    pre_roll_ms: int = 240
    partial_every_ms: int = 400

    @property
    def frame_ms(self) -> float:
        return 1000.0 * self.frame_samples / self.sample_rate

    def _frames(self, ms: int) -> int:
        return max(1, round(ms / self.frame_ms))


class Endpointer:
    """Feed it frames + speech probabilities, get utterances out."""

    def __init__(self, config: EndpointerConfig | None = None) -> None:
        self.cfg = config or EndpointerConfig()
        self._pre_roll: list[np.ndarray] = []
        self._pre_roll_max = self.cfg._frames(self.cfg.pre_roll_ms)
        self._buffer: list[np.ndarray] = []
        self._in_speech = False
        self._speech_run = 0
        self._silence_run = 0
        self._speech_frames = 0
        self._frames_since_partial = 0
        self._clock = 0.0

    # -- introspection used by the GUI meter -------------------------------
    @property
    def in_speech(self) -> bool:
        return self._in_speech

    def reset(self) -> None:
        self._pre_roll.clear()
        self._buffer.clear()
        self._in_speech = False
        self._speech_run = self._silence_run = self._speech_frames = 0
        self._frames_since_partial = 0

    def push(self, frame: np.ndarray, speech_prob: float) -> list[Event]:
        cfg = self.cfg
        self._clock += cfg.frame_ms / 1000.0
        events: list[Event] = []
        is_speech = speech_prob >= cfg.threshold

        if is_speech:
            self._speech_run += 1
            self._silence_run = 0
        else:
            self._silence_run += 1
            self._speech_run = 0

        if not self._in_speech:
            self._pre_roll.append(frame)
            if len(self._pre_roll) > self._pre_roll_max:
                self._pre_roll.pop(0)
            if self._speech_run >= cfg._frames(cfg.start_ms):
                self._in_speech = True
                self._buffer = list(self._pre_roll)
                self._pre_roll.clear()
                self._speech_frames = self._speech_run
                self._frames_since_partial = 0
                events.append(SpeechStarted(self._clock))
            return events

        self._buffer.append(frame)
        self._frames_since_partial += 1
        if is_speech:
            self._speech_frames += 1

        spoken_ms = self._speech_frames * cfg.frame_ms
        buffered_ms = len(self._buffer) * cfg.frame_ms

        if self._silence_run >= cfg._frames(cfg.endpoint_ms):
            if spoken_ms >= cfg.min_speech_ms:
                events.append(Utterance(self._concat(), self._clock, "endpoint"))
            self._drop()
            return events

        if buffered_ms >= cfg.max_utterance_ms:
            events.append(Utterance(self._concat(), self._clock, "max_length"))
            # Keep the tail as pre-roll: the speaker is mid-sentence and the
            # next segment must not start on a clipped syllable.
            self._drop()
            return events

        if (
            cfg.partial_every_ms > 0
            and self._frames_since_partial >= cfg._frames(cfg.partial_every_ms)
            and spoken_ms >= cfg.min_speech_ms
        ):
            self._frames_since_partial = 0
            events.append(Partial(self._concat(), self._clock))

        return events

    # -- internals ---------------------------------------------------------
    def _concat(self) -> np.ndarray:
        if not self._buffer:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._buffer).astype(np.float32, copy=False)

    def _drop(self) -> None:
        # Seed the next pre-roll from the trailing frames we just consumed so a
        # forced cut mid-sentence does not lose the following onset.
        tail = self._buffer[-self._pre_roll_max :] if self._buffer else []
        self._buffer = []
        self._pre_roll = list(tail)
        self._in_speech = False
        self._speech_frames = 0
        self._frames_since_partial = 0
