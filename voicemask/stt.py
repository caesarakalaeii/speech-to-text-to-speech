"""Speech recognition.

Parakeet TDT 0.6B v2 via onnx-asr. Chosen over Whisper because it is both
faster and more accurate here: measured on an i7-11700K (slower than the target
machine) it transcribes 2.4 s of speech in ~190 ms against Whisper-base's
~600 ms, and it emits punctuation and casing, which the synthesiser needs to
produce natural prosody. See docs/adr/0003-speech-recognition-model.md.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import numpy as np

from . import models, runtime, text

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000


@dataclass(frozen=True)
class Transcript:
    text: str
    latency_s: float
    audio_s: float


class Recogniser:
    def __init__(
        self,
        model_name: str = models.STT_MODEL,
        use_gpu: bool = False,
        quantization: str | None = None,
        threads: int = 0,
    ) -> None:
        import onnx_asr

        log.info("Loading recogniser %s (gpu=%s)", model_name, use_gpu)
        started = time.perf_counter()
        self._model = onnx_asr.load_model(
            model_name,
            quantization=quantization,
            sess_options=runtime.session_options(threads),
            providers=runtime.providers(use_gpu),
        )
        log.info("Recogniser ready in %.1fs", time.perf_counter() - started)

    def transcribe(self, audio: np.ndarray) -> Transcript:
        """Transcribe mono float32 audio at 16 kHz."""
        audio = np.asarray(audio, dtype=np.float32)
        started = time.perf_counter()
        raw = self._model.recognize(audio, sample_rate=SAMPLE_RATE)
        latency = time.perf_counter() - started
        return Transcript(
            text=text.clean(raw if isinstance(raw, str) else str(raw)),
            latency_s=latency,
            audio_s=len(audio) / SAMPLE_RATE,
        )
