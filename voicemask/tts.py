"""Speech synthesis.

Kokoro-82M via ONNX Runtime. It is Apache-2.0, ships 54 voices in a single
28 MB pack, and synthesises well faster than real time on CPU, which is what
makes the "pick a voice from a dropdown" experience possible without a model
download per voice. See docs/adr/0004-speech-synthesis-model.md.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import models, paths, runtime

log = logging.getLogger(__name__)

SAMPLE_RATE = 24000


@dataclass(frozen=True)
class Voice:
    """A selectable voice, as shown in the GUI."""

    id: str
    label: str
    accent: str
    gender: str
    grade: str  # Kokoro's own quality grade from the model card

    @property
    def display(self) -> str:
        return f"{self.label} — {self.accent} {self.gender}"


# Kokoro's voice ids encode accent and gender: a=American, b=British,
# f=female, m=male. Grades are from the upstream model card and correlate well
# with how natural each voice actually sounds; the GUI sorts by them so the
# best voices are at the top rather than in alphabetical order.
_ENGLISH_VOICES = [
    ("af_heart", "Heart", "American", "female", "A"),
    ("af_bella", "Bella", "American", "female", "A-"),
    ("af_nicole", "Nicole", "American", "female", "B-"),
    ("bf_emma", "Emma", "British", "female", "B-"),
    ("af_aoede", "Aoede", "American", "female", "C+"),
    ("af_kore", "Kore", "American", "female", "C+"),
    ("af_sarah", "Sarah", "American", "female", "C+"),
    ("am_fenrir", "Fenrir", "American", "male", "C+"),
    ("am_michael", "Michael", "American", "male", "C+"),
    ("am_puck", "Puck", "American", "male", "C+"),
    ("bf_isabella", "Isabella", "British", "female", "C"),
    ("bm_fable", "Fable", "British", "male", "C"),
    ("bm_george", "George", "British", "male", "C"),
    ("af_nova", "Nova", "American", "female", "C"),
    ("af_river", "River", "American", "female", "C"),
    ("af_sky", "Sky", "American", "female", "C-"),
    ("am_echo", "Echo", "American", "male", "D"),
    ("am_eric", "Eric", "American", "male", "D"),
    ("am_liam", "Liam", "American", "male", "D"),
    ("am_onyx", "Onyx", "American", "male", "D"),
    ("bf_alice", "Alice", "British", "female", "D"),
    ("bf_lily", "Lily", "British", "female", "D"),
    ("bm_daniel", "Daniel", "British", "male", "D"),
    ("bm_lewis", "Lewis", "British", "male", "D+"),
]

ENGLISH_VOICES: list[Voice] = [Voice(*v) for v in _ENGLISH_VOICES]
VOICES_BY_ID: dict[str, Voice] = {v.id: v for v in ENGLISH_VOICES}
DEFAULT_VOICE = "af_heart"


def voice_display(voice_id: str) -> str:
    voice = VOICES_BY_ID.get(voice_id) or _piper_by_id().get(voice_id)
    return voice.display if voice else voice_id


def _piper_by_id() -> dict[str, Voice]:
    from .tts_piper import PIPER_VOICES

    return {v.id: v for v in PIPER_VOICES}


def is_known_voice(voice_id: str) -> bool:
    return voice_id in VOICES_BY_ID or voice_id in _piper_by_id()


@dataclass(frozen=True)
class Speech:
    audio: np.ndarray
    sample_rate: int
    latency_s: float

    @property
    def duration_s(self) -> float:
        return len(self.audio) / self.sample_rate


class Synthesiser:
    def __init__(self, use_gpu: bool = False, threads: int = 0) -> None:
        import espeakng_loader
        import onnxruntime as ort
        from kokoro_onnx import Kokoro
        from kokoro_onnx.config import EspeakConfig

        model_path = models.asset_path("kokoro")
        voices_path = models.asset_path("kokoro_voices")
        if not model_path.exists() or not voices_path.exists():
            raise FileNotFoundError(
                "Kokoro model files are missing. Run the setup step first."
            )

        # See paths.safe_espeak_data_path for why this is not just the
        # library's own default.
        espeak = EspeakConfig(
            lib_path=str(espeakng_loader.get_library_path()),
            data_path=paths.safe_espeak_data_path(espeakng_loader.get_data_path()),
        )

        log.info("Loading synthesiser (gpu=%s)", use_gpu)
        started = time.perf_counter()
        self._kokoro = Kokoro(str(model_path), str(voices_path), espeak_config=espeak)
        # kokoro-onnx builds its own session with defaults; replace it with one
        # tuned for single-request latency and the provider we actually want.
        self._kokoro.sess = ort.InferenceSession(
            str(model_path),
            runtime.session_options(threads),
            providers=runtime.providers(use_gpu),
        )
        log.info("Synthesiser ready in %.1fs", time.perf_counter() - started)

    def voices(self) -> list[Voice]:
        available = set(self._kokoro.get_voices())
        return [v for v in ENGLISH_VOICES if v.id in available]

    def synthesise(self, text: str, voice: str, speed: float = 1.0) -> Speech:
        started = time.perf_counter()
        audio, sample_rate = self._kokoro.create(
            text, voice=voice, speed=speed, lang="en-us"
        )
        return Speech(
            audio=np.asarray(audio, dtype=np.float32),
            sample_rate=int(sample_rate),
            latency_s=time.perf_counter() - started,
        )

    def warm_up(self, voice: str = DEFAULT_VOICE) -> None:
        """First synthesis allocates buffers and is ~2x slower. Pay it now."""
        self.synthesise("Ready.", voice=voice)


class VoiceRouter:
    """Dispatch synthesis to whichever engine owns the selected voice.

    Voices from both engines share one dropdown -- a "fast mode" toggle would
    be one more thing to explain -- so the engine is inferred from the voice
    id and loaded on first use. If Piper is not installed, or its voice fails
    to load, we fall back to Kokoro rather than going silent mid-stream.
    """

    def __init__(self, use_gpu: bool = False, threads: int = 0) -> None:
        self._use_gpu = use_gpu
        self._threads = threads
        self._kokoro: Synthesiser | None = None
        self._piper: dict[str, object] = {}

    def _engine_for(self, voice: str):
        from .tts_piper import PiperSynthesiser, is_piper_voice

        if is_piper_voice(voice):
            if voice not in self._piper:
                try:
                    self._piper[voice] = PiperSynthesiser(voice)
                except Exception as exc:
                    log.warning("Piper voice %s unavailable (%s); using Kokoro", voice, exc)
                    self._piper[voice] = None
            engine = self._piper[voice]
            if engine is not None:
                return engine, voice
            voice = DEFAULT_VOICE

        if self._kokoro is None:
            self._kokoro = Synthesiser(self._use_gpu, self._threads)
        return self._kokoro, voice

    def synthesise(self, text: str, voice: str, speed: float = 1.0) -> Speech:
        engine, resolved = self._engine_for(voice)
        return engine.synthesise(text, voice=resolved, speed=speed)

    def warm_up(self, voice: str = DEFAULT_VOICE) -> None:
        engine, resolved = self._engine_for(voice)
        engine.warm_up(resolved)


def all_voices() -> list[Voice]:
    """Every selectable voice, best quality first, fast voices last."""
    from .tts_piper import PIPER_VOICES

    return [*ENGLISH_VOICES, *PIPER_VOICES]
