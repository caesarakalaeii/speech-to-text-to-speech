"""The real-time pipeline: microphone in, a different voice out.

Four stages, each on its own thread so that none of them blocks the audio
callbacks:

    capture ──frames──▶ VAD/endpoint ──audio──▶ recogniser ──text──▶ synthesiser ──▶ player

The interesting part is that the recogniser runs *while you are still talking*.
Every `partial_every_ms` it transcribes the audio so far;
:class:`~voicemask.text.LocalAgreement` works out which words two consecutive
guesses agree on, and only those get synthesised. By the time you stop
speaking, most of your sentence has already been spoken in the new voice, so
the delay the listener perceives is far shorter than the sum of the stages.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from . import segmenter as seg
from . import text as textutil
from .audio.capture import MicCapture
from .audio.playback import Player
from .config import Settings
from .stt import Recogniser
from .tts import Synthesiser
from .vad import HOP, SAMPLE_RATE, SileroVad

log = logging.getLogger(__name__)


# -- events surfaced to the GUI ------------------------------------------------
@dataclass(frozen=True)
class Status:
    message: str


@dataclass(frozen=True)
class Heard:
    """Text the recogniser is confident about."""

    text: str


@dataclass(frozen=True)
class Spoke:
    """Text handed to the synthesiser and now audible."""

    text: str


@dataclass(frozen=True)
class Level:
    rms: float
    speech: bool


@dataclass(frozen=True)
class Failed:
    message: str


@dataclass
class Stats:
    utterances: int = 0
    stt_ms: float = 0.0
    tts_ms: float = 0.0
    response_ms: float = 0.0
    dropped_frames: int = 0
    _stt: deque[float] = field(default_factory=lambda: deque(maxlen=20))
    _tts: deque[float] = field(default_factory=lambda: deque(maxlen=20))
    _resp: deque[float] = field(default_factory=lambda: deque(maxlen=20))

    def record_stt(self, seconds: float) -> None:
        self._stt.append(seconds * 1000)
        self.stt_ms = sum(self._stt) / len(self._stt)

    def record_tts(self, seconds: float) -> None:
        self._tts.append(seconds * 1000)
        self.tts_ms = sum(self._tts) / len(self._tts)

    def record_response(self, seconds: float) -> None:
        self._resp.append(seconds * 1000)
        self.response_ms = sum(self._resp) / len(self._resp)


Event = Status | Heard | Spoke | Level | Failed
EventFn = Callable[[Event], None]


@dataclass
class _Chunk:
    text: str
    utterance: int
    final: bool
    ended_at: float | None


class Pipeline:
    def __init__(
        self,
        settings: Settings,
        recogniser: Recogniser,
        synthesiser: Synthesiser,
        vad: SileroVad,
        capture: MicCapture,
        player: Player,
        on_event: EventFn | None = None,
        echo_guard: bool = False,
    ) -> None:
        self.settings = settings
        self.stats = Stats()
        self._recogniser = recogniser
        self._synthesiser = synthesiser
        self._vad = vad
        self._capture = capture
        self._player = player
        self._emit = on_event or (lambda event: None)
        self._echo_guard = echo_guard

        self._endpointer = seg.Endpointer(
            seg.EndpointerConfig(
                sample_rate=SAMPLE_RATE,
                frame_samples=HOP,
                threshold=settings.vad_threshold,
                endpoint_ms=settings.endpoint_ms,
                min_speech_ms=settings.min_speech_ms,
                max_utterance_ms=settings.max_utterance_ms,
                partial_every_ms=settings.partial_every_ms if settings.streaming else 0,
            )
        )
        self._agreement = textutil.LocalAgreement()
        self._speech_buffer = textutil.SpeechBuffer()

        self._segments: queue.Queue[seg.Event] = queue.Queue(maxsize=32)
        self._chunks: queue.Queue[_Chunk] = queue.Queue(maxsize=32)
        self._running = threading.Event()
        self._threads: list[threading.Thread] = []
        self._utterance = 0
        self._audible_since: dict[int, bool] = {}

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        self._capture.start()
        self._player.start()
        for name, target in (
            ("vad", self._vad_loop),
            ("asr", self._asr_loop),
            ("tts", self._tts_loop),
        ):
            thread = threading.Thread(target=target, name=f"voicemask-{name}", daemon=True)
            thread.start()
            self._threads.append(thread)
        self._emit(Status("Listening"))

    def stop(self) -> None:
        if not self._running.is_set():
            return
        self._running.clear()
        for thread in self._threads:
            thread.join(timeout=3.0)
        self._threads.clear()
        self._capture.stop()
        self._player.stop()
        self._emit(Status("Stopped"))

    @property
    def running(self) -> bool:
        return self._running.is_set()

    # -- stage 1: voice activity + endpointing -----------------------------
    def _vad_loop(self) -> None:
        while self._running.is_set():
            frame = self._capture.read(timeout=0.1)
            if frame is None:
                continue

            # Do not listen to ourselves. Only relevant when output goes to a
            # real speaker rather than a virtual cable.
            if self._echo_guard and self._player.queued_s > 0.05:
                if self._endpointer.in_speech:
                    self._endpointer.reset()
                    self._vad.reset()
                continue

            try:
                probability = self._vad(frame)
            except Exception as exc:  # pragma: no cover - model level failure
                log.exception("VAD failed")
                self._emit(Failed(f"Voice detection failed: {exc}"))
                return

            self._emit(Level(float(np.sqrt(np.mean(frame**2))), probability >= self.settings.vad_threshold))

            for event in self._endpointer.push(frame, probability):
                try:
                    self._segments.put_nowait(event)
                except queue.Full:
                    self.stats.dropped_frames += 1

        self.stats.dropped_frames += self._capture.overflows

    # -- stage 2: recognition ---------------------------------------------
    def _asr_loop(self) -> None:
        while self._running.is_set():
            event = self._next_segment()
            if event is None:
                continue
            try:
                if isinstance(event, seg.SpeechStarted):
                    self._utterance += 1
                    self._agreement.reset()
                elif isinstance(event, seg.Partial):
                    self._on_partial(event)
                elif isinstance(event, seg.Utterance):
                    self._on_utterance(event)
            except Exception as exc:  # pragma: no cover
                log.exception("Recognition failed")
                self._emit(Failed(f"Recognition failed: {exc}"))

    def _next_segment(self) -> seg.Event | None:
        """Take the next event, discarding stale partials.

        A partial is only useful if it is the newest one. If recognition fell
        behind -- a long utterance costs more per pass -- processing the backlog
        would push us further behind on every pass.
        """
        try:
            event = self._segments.get(timeout=0.1)
        except queue.Empty:
            return None
        while isinstance(event, seg.Partial):
            try:
                nxt = self._segments.get_nowait()
            except queue.Empty:
                break
            event = nxt
        return event

    def _on_partial(self, event: seg.Partial) -> None:
        transcript = self._recogniser.transcribe(event.audio)
        self.stats.record_stt(transcript.latency_s)
        if textutil.is_hallucination(transcript.text):
            return
        committed = self._agreement.insert(transcript.text)
        if not committed:
            return
        self._emit(Heard(committed))
        for chunk in self._speech_buffer.add(committed):
            self._enqueue(chunk, final=False, ended_at=None)

    def _on_utterance(self, event: seg.Utterance) -> None:
        transcript = self._recogniser.transcribe(event.audio)
        self.stats.record_stt(transcript.latency_s)
        self.stats.utterances += 1

        if textutil.is_hallucination(transcript.text):
            self._agreement.reset()
            self._speech_buffer.flush()
            return

        tail = self._agreement.finalise(transcript.text)
        ended_at = time.perf_counter()

        # `add` releases any chunk that is already complete and removes it from
        # the buffer, so its return value has to be kept -- `flush` only sees
        # what is left over. Dropping it silently loses whole sentences
        # whenever the final pass ends on punctuation.
        remaining: list[str] = []
        if tail:
            self._emit(Heard(tail))
            remaining.extend(self._speech_buffer.add(tail))
        remaining.extend(self._speech_buffer.flush())

        for index, chunk in enumerate(remaining):
            self._enqueue(chunk, final=index == len(remaining) - 1, ended_at=ended_at)

    def _enqueue(self, chunk_text: str, final: bool, ended_at: float | None) -> None:
        if not chunk_text.strip():
            return
        try:
            self._chunks.put_nowait(
                _Chunk(chunk_text, self._utterance, final, ended_at)
            )
        except queue.Full:
            log.warning("Synthesis backlog full; dropping %r", chunk_text)

    # -- stage 3: synthesis + playback -------------------------------------
    def _tts_loop(self) -> None:
        while self._running.is_set():
            try:
                chunk = self._chunks.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                # Audio already flowing for this utterance means the listener
                # is mid-sentence and hears no gap at all.
                already_audible = self._player.queued_s > 0.02
                speech = self._synthesiser.synthesise(
                    chunk.text, voice=self.settings.voice, speed=self.settings.speed
                )
                self.stats.record_tts(speech.latency_s)
                self._player.play(speech.audio, speech.sample_rate)
                self._emit(Spoke(chunk.text))

                if chunk.ended_at is not None:
                    self.stats.record_response(
                        0.0 if already_audible else time.perf_counter() - chunk.ended_at
                    )
            except Exception as exc:  # pragma: no cover
                log.exception("Synthesis failed")
                self._emit(Failed(f"Synthesis failed: {exc}"))
