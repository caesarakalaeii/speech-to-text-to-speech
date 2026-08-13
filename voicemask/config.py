"""User settings, persisted as JSON next to the models."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from . import paths, tts

log = logging.getLogger(__name__)


@dataclass
class Settings:
    # -- devices. Stored by name, not index: PortAudio indices change every
    #    time a USB headset is plugged in.
    input_device: str | None = None
    output_device: str | None = None
    monitor_device: str | None = None

    # -- voice
    voice: str = tts.DEFAULT_VOICE
    speed: float = 1.0
    volume: float = 1.0
    monitor_volume: float = 0.7

    # -- responsiveness. endpoint_ms is the one to reach for: it is how long
    #    the app waits for you to stop talking, and it dominates end-to-end
    #    latency. Below ~250 ms it starts cutting people off mid-sentence.
    endpoint_ms: int = 320
    vad_threshold: float = 0.5
    min_speech_ms: int = 200
    max_utterance_ms: int = 12000

    # -- speculative transcription while you are still speaking. This is what
    #    gets the perceived delay under half a second; turning it off is
    #    slower but uses less CPU.
    streaming: bool = True
    partial_every_ms: int = 400

    # -- "auto" enables it only when the output is a real speaker (where the
    #    mic could hear the synthesised voice and transcribe it back).
    echo_guard: str = "auto"  # auto | on | off

    mic_gain: float = 1.0
    use_gpu: bool = False

    @classmethod
    def load(cls, path: Path | None = None) -> Settings:
        path = path or paths.settings_path()
        if not path.exists():
            return cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("Could not read settings (%s); using defaults", exc)
            return cls()
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in raw.items() if k in known})

    def save(self, path: Path | None = None) -> None:
        path = path or paths.settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def validated(self) -> Settings:
        """Clamp values into ranges the audio pipeline can actually honour."""
        self.speed = _clamp(self.speed, 0.5, 2.0)
        self.volume = _clamp(self.volume, 0.0, 2.0)
        self.monitor_volume = _clamp(self.monitor_volume, 0.0, 2.0)
        self.mic_gain = _clamp(self.mic_gain, 0.1, 8.0)
        self.vad_threshold = _clamp(self.vad_threshold, 0.1, 0.9)
        self.endpoint_ms = int(_clamp(self.endpoint_ms, 150, 2000))
        self.min_speech_ms = int(_clamp(self.min_speech_ms, 60, 2000))
        self.max_utterance_ms = int(_clamp(self.max_utterance_ms, 2000, 30000))
        self.partial_every_ms = int(_clamp(self.partial_every_ms, 200, 2000))
        if not tts.is_known_voice(self.voice):
            self.voice = tts.DEFAULT_VOICE
        if self.echo_guard not in {"auto", "on", "off"}:
            self.echo_guard = "auto"
        return self


def _clamp(value: float, low: float, high: float) -> float:
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return low
