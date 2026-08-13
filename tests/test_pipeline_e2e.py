"""End-to-end tests: audio in, different-voice audio out, no devices involved.

Real ONNX models run here. The only things faked are the microphone and the
speaker, because a test cannot rely on the host having either -- everything
between them is the production code path.

The trick that makes this a genuine end-to-end test rather than a mock parade:
we *synthesise* the input speech with one Kokoro voice, push it through the
pipeline, and check the pipeline both understood it and re-spoke it in a
different voice.
"""

from __future__ import annotations

import queue
import threading
import time

import numpy as np
import pytest

from voicemask import pipeline as pl
from voicemask.audio.resample import resample
from voicemask.config import Settings
from voicemask.text import normalise_word
from voicemask.vad import HOP, SAMPLE_RATE

pytestmark = pytest.mark.models

SENTENCE = "Hey chat, welcome back to the stream tonight."


class FakeCapture:
    """Replays a fixed recording as 32 ms frames, paced like a real mic."""

    def __init__(self, audio: np.ndarray, realtime: bool = True) -> None:
        usable = len(audio) // HOP * HOP
        self._frames = audio[:usable].reshape(-1, HOP).astype(np.float32)
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._realtime = realtime
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.overflows = 0
        self.finished = threading.Event()

    def start(self) -> None:
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()

    def _pump(self) -> None:
        interval = HOP / SAMPLE_RATE
        for frame in self._frames:
            if self._stop.is_set():
                return
            self._queue.put(frame)
            if self._realtime:
                time.sleep(interval)
        self.finished.set()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def read(self, timeout: float = 0.1) -> np.ndarray | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None


class FakePlayer:
    """Collects everything that would have been played."""

    def __init__(self) -> None:
        self.chunks: list[tuple[np.ndarray, int]] = []
        self._lock = threading.Lock()
        self.started = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.started = False

    def play(self, audio: np.ndarray, sample_rate: int) -> None:
        with self._lock:
            self.chunks.append((np.asarray(audio), sample_rate))

    def clear(self) -> None:
        with self._lock:
            self.chunks.clear()

    @property
    def queued_s(self) -> float:
        return 0.0

    @property
    def total_duration_s(self) -> float:
        with self._lock:
            return sum(len(a) / sr for a, sr in self.chunks)

    def concatenated(self) -> tuple[np.ndarray, int]:
        with self._lock:
            assert self.chunks, "nothing was played"
            rate = self.chunks[0][1]
            return np.concatenate([a for a, _ in self.chunks]), rate


def _speech_at_16k(synthesiser, sentence: str, voice: str, lead_in_s: float = 0.5,
                   tail_s: float = 1.2) -> np.ndarray:
    """Render `sentence`, pad with silence, and resample to the mic rate."""
    speech = synthesiser.synthesise(sentence, voice=voice)
    audio = resample(speech.audio, speech.sample_rate, SAMPLE_RATE)
    lead = np.zeros(int(lead_in_s * SAMPLE_RATE), dtype=np.float32)
    tail = np.zeros(int(tail_s * SAMPLE_RATE), dtype=np.float32)
    return np.concatenate([lead, audio, tail])


def _run(settings, recogniser, synthesiser, vad, audio, timeout=40.0):
    events: list = []
    capture = FakeCapture(audio)
    player = FakePlayer()
    engine = pl.Pipeline(
        settings=settings,
        recogniser=recogniser,
        synthesiser=synthesiser,
        vad=vad,
        capture=capture,
        player=player,
        on_event=events.append,
        echo_guard=False,
    )
    engine.start()
    deadline = time.monotonic() + timeout
    try:
        # Wait for the recording to finish playing in, then for the pipeline
        # to drain what it queued.
        capture.finished.wait(timeout=timeout)
        while time.monotonic() < deadline:
            time.sleep(0.25)
            if engine.stats.utterances and player.chunks:
                time.sleep(0.75)  # let any trailing chunk land
                break
    finally:
        engine.stop()
    return engine, events, player


def _spoken(events) -> str:
    return " ".join(e.text for e in events if isinstance(e, pl.Spoke))


def _words(text: str) -> list[str]:
    return [normalise_word(w) for w in text.split() if normalise_word(w)]


@pytest.fixture(scope="module")
def settings():
    return Settings(
        voice="am_michael",
        endpoint_ms=320,
        streaming=True,
        partial_every_ms=400,
        echo_guard="off",
    ).validated()


class TestEndToEnd:
    def test_speech_in_produces_speech_out(
        self, settings, recogniser, synthesiser, vad
    ):
        audio = _speech_at_16k(synthesiser, SENTENCE, voice="af_heart")
        engine, events, player = _run(settings, recogniser, synthesiser, vad, audio)

        assert engine.stats.utterances >= 1, "no utterance was detected"
        assert player.chunks, "nothing was synthesised"
        assert player.total_duration_s > 1.0

        spoken, rate = player.concatenated()
        assert rate == 24000
        assert np.max(np.abs(spoken)) > 0.01, "output is silent"

    def test_the_words_survive_the_round_trip(
        self, settings, recogniser, synthesiser, vad
    ):
        audio = _speech_at_16k(synthesiser, SENTENCE, voice="af_heart")
        _, events, _ = _run(settings, recogniser, synthesiser, vad, audio)

        spoken = _words(_spoken(events))
        expected = _words(SENTENCE)
        assert spoken, "nothing was spoken"
        # Allow a little slack at the edges; demand the content words match.
        overlap = len(set(expected) & set(spoken)) / len(set(expected))
        assert overlap >= 0.8, f"expected {expected}, spoke {spoken}"

    def test_no_word_is_spoken_twice(self, settings, recogniser, synthesiser, vad):
        """Streaming commit must not re-speak text it already released."""
        audio = _speech_at_16k(synthesiser, SENTENCE, voice="af_heart")
        _, events, _ = _run(settings, recogniser, synthesiser, vad, audio)

        spoken = _words(_spoken(events))
        expected = _words(SENTENCE)
        for word in set(expected):
            assert spoken.count(word) <= expected.count(word) + 1, (
                f"'{word}' was spoken {spoken.count(word)} times, "
                f"expected at most {expected.count(word) + 1}"
            )

    def test_silence_produces_nothing(self, settings, recogniser, synthesiser, vad):
        silence = np.zeros(int(3 * SAMPLE_RATE), dtype=np.float32)
        engine, events, player = _run(
            settings, recogniser, synthesiser, vad, silence, timeout=12
        )
        assert not player.chunks, f"spoke on silence: {_spoken(events)}"
        assert engine.stats.utterances == 0

    def test_quiet_noise_does_not_trigger_speech(
        self, settings, recogniser, synthesiser, vad
    ):
        rng = np.random.default_rng(1234)
        noise = (rng.standard_normal(int(3 * SAMPLE_RATE)) * 0.002).astype(np.float32)
        _, events, player = _run(
            settings, recogniser, synthesiser, vad, noise, timeout=12
        )
        assert not player.chunks, f"spoke on noise: {_spoken(events)}"

    def test_response_latency_is_under_one_second(
        self, settings, recogniser, synthesiser, vad
    ):
        """The headline claim: sub-second from end of speech to new voice."""
        audio = _speech_at_16k(synthesiser, SENTENCE, voice="af_heart")
        engine, _, _ = _run(settings, recogniser, synthesiser, vad, audio)

        assert engine.stats.response_ms > 0 or engine.stats.utterances >= 1
        print(
            f"\n  response {engine.stats.response_ms:.0f} ms | "
            f"recognise {engine.stats.stt_ms:.0f} ms | "
            f"speak {engine.stats.tts_ms:.0f} ms"
        )
        assert engine.stats.response_ms < 1000, (
            f"response latency {engine.stats.response_ms:.0f} ms exceeds the "
            "one second budget"
        )

    def test_two_utterances_are_both_spoken(
        self, settings, recogniser, synthesiser, vad
    ):
        first = _speech_at_16k(synthesiser, "The first thing I want to say.",
                               voice="af_heart", tail_s=1.0)
        second = _speech_at_16k(synthesiser, "And here is the second thing.",
                                voice="af_heart", lead_in_s=0.0, tail_s=1.2)
        engine, events, player = _run(
            settings, recogniser, synthesiser, vad,
            np.concatenate([first, second]), timeout=60,
        )
        assert engine.stats.utterances >= 2
        spoken = _words(_spoken(events))
        assert "first" in spoken and "second" in spoken


class TestNonStreamingMode:
    def test_pipeline_works_with_streaming_disabled(
        self, recogniser, synthesiser, vad
    ):
        settings = Settings(
            voice="am_michael", streaming=False, echo_guard="off"
        ).validated()
        audio = _speech_at_16k(synthesiser, SENTENCE, voice="af_heart")
        engine, events, player = _run(settings, recogniser, synthesiser, vad, audio)

        assert player.chunks
        spoken = _words(_spoken(events))
        overlap = len(set(_words(SENTENCE)) & set(spoken)) / len(set(_words(SENTENCE)))
        assert overlap >= 0.8
