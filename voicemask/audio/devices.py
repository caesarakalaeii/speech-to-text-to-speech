"""Audio device enumeration and virtual-cable detection."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

log = logging.getLogger(__name__)

# Names used by the common Windows virtual audio drivers. Routing VoiceMask's
# output into one of these is what makes the masked voice show up as a
# microphone in OBS, Discord or a browser.
_VIRTUAL_CABLE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"cable input",  # VB-CABLE playback endpoint
        r"cable output",  # VB-CABLE capture endpoint
        r"vb-audio",
        r"voicemeeter",
        r"virtual audio cable",
        r"\bvac\b",
    )
]


@dataclass(frozen=True)
class Device:
    index: int
    name: str
    channels: int
    default_samplerate: float
    hostapi: str
    is_input: bool

    @property
    def is_virtual_cable(self) -> bool:
        return any(p.search(self.name) for p in _VIRTUAL_CABLE_PATTERNS)

    @property
    def display(self) -> str:
        suffix = "  [virtual cable]" if self.is_virtual_cable else ""
        return f"{self.name} ({self.hostapi}){suffix}"


def _devices(want_input: bool) -> list[Device]:
    import sounddevice as sd

    hostapis = sd.query_hostapis()
    out: list[Device] = []
    for index, info in enumerate(sd.query_devices()):
        channels = info["max_input_channels" if want_input else "max_output_channels"]
        if channels < 1:
            continue
        out.append(
            Device(
                index=index,
                name=info["name"],
                channels=channels,
                default_samplerate=info["default_samplerate"],
                hostapi=hostapis[info["hostapi"]]["name"],
                is_input=want_input,
            )
        )
    return out


def input_devices() -> list[Device]:
    return _devices(want_input=True)


def output_devices() -> list[Device]:
    return _devices(want_input=False)


def default_input() -> Device | None:
    return _default(want_input=True)


def default_output() -> Device | None:
    return _default(want_input=False)


def _default(want_input: bool) -> Device | None:
    import sounddevice as sd

    try:
        index = sd.default.device[0 if want_input else 1]
    except Exception:  # pragma: no cover - depends on host audio stack
        index = None
    devices = _devices(want_input)
    if index is not None and index >= 0:
        for device in devices:
            if device.index == index:
                return device
    return devices[0] if devices else None


def find_by_name(name: str | None, want_input: bool) -> Device | None:
    """Resolve a stored device *name* back to a device.

    Settings store names rather than indices on purpose: PortAudio indices
    shift whenever a USB headset is plugged in, and a streamer replugs
    constantly. An exact match wins; otherwise fall back to a unique substring
    match so a slightly renamed device still resolves.
    """
    if not name:
        return None
    devices = _devices(want_input)
    for device in devices:
        if device.name == name:
            return device
    partial = [d for d in devices if name.lower() in d.name.lower()]
    if len(partial) == 1:
        return partial[0]
    log.warning("Audio device %r not found; falling back to system default", name)
    return None


def virtual_cable_output() -> Device | None:
    """The playback endpoint that feeds a virtual cable, if one is installed."""
    for device in output_devices():
        if device.is_virtual_cable and "output" not in device.name.lower():
            return device
    for device in output_devices():
        if device.is_virtual_cable:
            return device
    return None


def has_virtual_cable() -> bool:
    return virtual_cable_output() is not None
