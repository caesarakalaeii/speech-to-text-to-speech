import numpy as np
import pytest

from voicemask.segmenter import (
    Endpointer,
    EndpointerConfig,
    Partial,
    SpeechStarted,
    Utterance,
)

FRAME = 512
RATE = 16000
FRAME_MS = 1000 * FRAME / RATE  # 32 ms


def cfg(**overrides) -> EndpointerConfig:
    base = dict(
        sample_rate=RATE,
        frame_samples=FRAME,
        threshold=0.5,
        start_ms=64,
        endpoint_ms=320,
        min_speech_ms=200,
        max_utterance_ms=12000,
        pre_roll_ms=240,
        partial_every_ms=0,  # off unless a test asks for it
    )
    base.update(overrides)
    return EndpointerConfig(**base)


def frames(count: int, value: float = 0.1) -> list[np.ndarray]:
    return [np.full(FRAME, value, dtype=np.float32) for _ in range(count)]


def feed(ep: Endpointer, count: int, prob: float, value: float = 0.1) -> list:
    events = []
    for frame in frames(count, value):
        events.extend(ep.push(frame, prob))
    return events


class TestSpeechDetection:
    def test_silence_produces_nothing(self):
        assert feed(Endpointer(cfg()), 100, prob=0.0) == []

    def test_speech_start_needs_consecutive_speech_frames(self):
        ep = Endpointer(cfg(start_ms=64))  # 2 frames
        assert feed(ep, 1, prob=0.9) == []
        events = feed(ep, 1, prob=0.9)
        assert [type(e) for e in events] == [SpeechStarted]

    def test_isolated_noise_spike_does_not_start_speech(self):
        ep = Endpointer(cfg(start_ms=64))
        events = []
        for prob in (0.9, 0.0, 0.9, 0.0, 0.9, 0.0):
            events.extend(feed(ep, 1, prob=prob))
        assert events == []


class TestEndpointing:
    def test_utterance_is_emitted_after_trailing_silence(self):
        ep = Endpointer(cfg(endpoint_ms=320))  # 10 frames
        feed(ep, 20, prob=0.9)  # 640 ms of speech
        assert feed(ep, 9, prob=0.0) == []  # not yet
        events = feed(ep, 1, prob=0.0)
        assert len(events) == 1 and isinstance(events[0], Utterance)
        assert events[0].reason == "endpoint"

    def test_too_short_speech_is_discarded(self):
        # A cough is two frames of "speech"; it must not reach the recogniser.
        ep = Endpointer(cfg(min_speech_ms=200, start_ms=64))
        feed(ep, 3, prob=0.9)  # 96 ms
        assert [e for e in feed(ep, 15, prob=0.0) if isinstance(e, Utterance)] == []

    def test_utterance_includes_pre_roll_before_speech_started(self):
        """Without pre-roll the first consonant is clipped and misrecognised."""
        ep = Endpointer(cfg(pre_roll_ms=240))  # ~7 frames
        feed(ep, 7, prob=0.0, value=0.5)  # quiet lead-in, distinct amplitude
        feed(ep, 20, prob=0.9, value=0.1)
        events = feed(ep, 12, prob=0.0)
        utterance = next(e for e in events if isinstance(e, Utterance))
        # The lead-in frames must be at the front of the captured audio.
        assert np.isclose(utterance.audio[0], 0.5)
        assert len(utterance.audio) > 20 * FRAME

    def test_endpoint_timer_resets_when_speech_resumes(self):
        ep = Endpointer(cfg(endpoint_ms=320))
        feed(ep, 20, prob=0.9)
        feed(ep, 5, prob=0.0)  # a pause, but not long enough
        feed(ep, 5, prob=0.9)  # keeps going
        assert [e for e in feed(ep, 5, prob=0.0) if isinstance(e, Utterance)] == []
        assert [e for e in feed(ep, 5, prob=0.0) if isinstance(e, Utterance)]

    def test_after_an_utterance_the_next_one_is_detected(self):
        ep = Endpointer(cfg())
        feed(ep, 20, prob=0.9)
        feed(ep, 12, prob=0.0)
        feed(ep, 20, prob=0.9)
        events = feed(ep, 12, prob=0.0)
        assert any(isinstance(e, Utterance) for e in events)


class TestMaxLength:
    def test_continuous_speech_is_cut_at_the_cap(self):
        # Someone who never pauses must still get their words through.
        ep = Endpointer(cfg(max_utterance_ms=1000))  # ~31 frames
        events = feed(ep, 60, prob=0.9)
        cuts = [e for e in events if isinstance(e, Utterance)]
        assert cuts and cuts[0].reason == "max_length"

    def test_speech_continues_to_be_captured_after_a_forced_cut(self):
        ep = Endpointer(cfg(max_utterance_ms=1000))
        events = feed(ep, 120, prob=0.9)
        assert len([e for e in events if isinstance(e, Utterance)]) >= 2


class TestPartials:
    def test_partials_are_emitted_while_speaking(self):
        ep = Endpointer(cfg(partial_every_ms=320))  # every 10 frames
        events = feed(ep, 40, prob=0.9)
        partials = [e for e in events if isinstance(e, Partial)]
        assert len(partials) >= 3

    def test_partial_audio_grows_monotonically(self):
        ep = Endpointer(cfg(partial_every_ms=320))
        events = feed(ep, 40, prob=0.9)
        sizes = [len(e.audio) for e in events if isinstance(e, Partial)]
        assert sizes == sorted(sizes)
        assert len(set(sizes)) == len(sizes)

    def test_no_partials_when_streaming_is_disabled(self):
        ep = Endpointer(cfg(partial_every_ms=0))
        events = feed(ep, 60, prob=0.9)
        assert not any(isinstance(e, Partial) for e in events)


def test_wrong_frame_size_is_rejected_by_the_vad_contract():
    from voicemask import vad

    assert vad.HOP == FRAME  # the endpointer default must match Silero's hop


@pytest.mark.parametrize("endpoint_ms", [200, 320, 500])
def test_endpoint_latency_matches_configuration(endpoint_ms):
    ep = Endpointer(cfg(endpoint_ms=endpoint_ms))
    feed(ep, 30, prob=0.9)
    silent = 0
    while True:
        silent += 1
        events = feed(ep, 1, prob=0.0)
        if any(isinstance(e, Utterance) for e in events):
            break
        assert silent < 100
    assert abs(silent * FRAME_MS - endpoint_ms) <= FRAME_MS
