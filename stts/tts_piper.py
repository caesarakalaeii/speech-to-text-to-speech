"""Piper synthesis -- the fast, lower-quality fallback.

Piper is substantially faster than Kokoro and each voice is a ~60 MB ONNX file,
but it sounds distinctly more synthetic. It earns its place for two situations:
a machine too slow for Kokoro to keep up, and as something that still works if
the Kokoro model or its phonemiser fails to load.

Note that the speed gap has not been benchmarked in this project -- `stts bench`
only exercises Kokoro -- so no ratio is quoted here or in the README. If that
number is ever needed, measure it and record it in ADR 4.

Installed on demand -- `pip install speech-to-text-to-speech[piper]` -- so the
default install does not carry it.
"""

from __future__ import annotations

import logging
import time
import urllib.request
from pathlib import Path

import numpy as np

from . import paths
from .tts import Speech, Voice

log = logging.getLogger(__name__)

_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"

# A deliberately short list: Piper has hundreds of voices and a dropdown with
# hundreds of entries is not a choice, it is a chore.
PIPER_VOICES = [
    Voice("piper:en_US-amy-medium", "Amy (fast)", "American", "female", "fast"),
    Voice("piper:en_US-ryan-medium", "Ryan (fast)", "American", "male", "fast"),
    Voice("piper:en_GB-alba-medium", "Alba (fast)", "British", "female", "fast"),
    Voice("piper:en_GB-northern_english_male-medium", "Ellis (fast)", "British", "male", "fast"),
]


def is_piper_voice(voice_id: str) -> bool:
    return voice_id.startswith("piper:")


def _voice_name(voice_id: str) -> str:
    return voice_id.removeprefix("piper:")


def _remote_path(name: str) -> str:
    """en_US-amy-medium -> en/en_US/amy/medium/en_US-amy-medium"""
    locale, speaker, quality = name.split("-", 2)
    language = locale.split("_")[0]
    return f"{language}/{locale}/{speaker}/{quality}/{name}"


def download_voice(voice_id: str) -> Path:
    name = _voice_name(voice_id)
    target = paths.models_dir() / "piper" / f"{name}.onnx"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.with_suffix(".onnx.json").exists():
        return target

    remote = _HF_BASE + _remote_path(name)
    log.info("Downloading Piper voice %s", name)
    for suffix in (".onnx", ".onnx.json"):
        destination = target.with_suffix(suffix) if suffix != ".onnx" else target
        temporary = destination.with_suffix(destination.suffix + ".part")
        urllib.request.urlretrieve(remote + suffix, temporary)
        temporary.replace(destination)
    return target


class PiperSynthesiser:
    def __init__(self, voice_id: str) -> None:
        from piper.voice import PiperVoice

        self.voice_id = voice_id
        path = download_voice(voice_id)
        log.info("Loading Piper voice %s", path.name)
        self._voice = PiperVoice.load(str(path))

    def voices(self) -> list[Voice]:
        return list(PIPER_VOICES)

    def synthesise(self, text: str, voice: str, speed: float = 1.0) -> Speech:
        started = time.perf_counter()
        chunks: list[np.ndarray] = []
        sample_rate = 22050
        for chunk in self._voice.synthesize(text):
            chunks.append(np.asarray(chunk.audio_float_array, dtype=np.float32))
            sample_rate = chunk.sample_rate or sample_rate

        audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
        # Piper has no speed control, so resample to change the rate. This
        # shifts pitch slightly, which is acceptable at the +/-20% people use.
        if speed != 1.0 and audio.size:
            from .audio.resample import resample

            audio = resample(audio, int(sample_rate * speed), sample_rate)
        return Speech(audio, sample_rate, time.perf_counter() - started)

    def warm_up(self, voice: str | None = None) -> None:
        self.synthesise("Ready.", voice=self.voice_id)
