"""Windows-specific helpers, chiefly the virtual microphone.

For a streamer, playing the masked voice out of a speaker is useless -- OBS and
Discord need it as a *microphone*. On Windows that means a virtual audio cable
driver. We do not bundle one: installing a kernel driver is the user's
decision, needs administrator rights, and the installer belongs to VB-Audio.
What we do is detect whether one is present, and if not, fetch the official
installer and hand it over with instructions.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

log = logging.getLogger(__name__)

VB_CABLE_PAGE = "https://vb-audio.com/Cable/"
VB_CABLE_ZIP = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip"

_EXPLAINER = (
    "This app needs a “virtual microphone” so OBS, Discord and your browser "
    "can hear the new voice instead of your real one.\n\n"
    "The standard free tool for this is VB-CABLE, made by VB-Audio.\n\n"
    "If you continue, it will be downloaded from vb-audio.com and their "
    "installer will open. You will need to:\n"
    "   1. Click “Yes” when Windows asks for permission\n"
    "   2. Click “Install Driver”\n"
    "   3. Restart your PC\n\n"
    "Those steps cannot be done for you — Windows requires you to approve "
    "driver installation yourself.\n\n"
    "Download and open the VB-CABLE installer now?"
)


def is_windows() -> bool:
    return os.name == "nt"


def guide_virtual_cable_install(parent=None) -> bool:
    """Offer to download and launch the VB-CABLE installer. Returns True if launched."""
    from tkinter import messagebox

    if not is_windows():
        messagebox.showinfo(
            "Speech-to-Text-to-Speech",
            "Virtual audio cables are handled differently outside Windows.\n\n"
            "On Linux use a PipeWire or PulseAudio null sink; on macOS use "
            "BlackHole. Then pick it as the output device.",
            parent=parent,
        )
        return False

    if not messagebox.askyesno("Set up virtual microphone", _EXPLAINER, parent=parent):
        return False

    try:
        installer = download_virtual_cable()
    except Exception as exc:
        log.exception("VB-CABLE download failed")
        messagebox.showerror(
            "Speech-to-Text-to-Speech",
            f"Could not download VB-CABLE ({exc}).\n\n"
            f"You can install it manually from {VB_CABLE_PAGE}",
            parent=parent,
        )
        return False

    try:
        # ShellExecute with the "runas" verb produces the standard Windows
        # elevation prompt. The user still approves it and still clicks
        # "Install Driver" in VB-Audio's own installer.
        import ctypes

        ctypes.windll.shell32.ShellExecuteW(None, "runas", str(installer), None,
                                            str(installer.parent), 1)
    except Exception as exc:
        log.exception("Could not launch VB-CABLE installer")
        messagebox.showerror(
            "Speech-to-Text-to-Speech",
            f"Downloaded the installer but could not open it ({exc}).\n\n"
            f"Run it yourself:\n{installer}",
            parent=parent,
        )
        return False

    messagebox.showinfo(
        "Almost done",
        "Finish the VB-CABLE installer, then restart your PC.\n\n"
        "After the restart, open this app and choose “CABLE Input” as where the "
        "voice goes. In OBS or Discord, choose “CABLE Output” as your "
        "microphone.",
        parent=parent,
    )
    return True


def download_virtual_cable(destination: Path | None = None) -> Path:
    """Download and extract the VB-CABLE driver pack; return the setup .exe."""
    destination = destination or Path(tempfile.gettempdir()) / "stts-vbcable"
    destination.mkdir(parents=True, exist_ok=True)

    archive = destination / "VBCABLE_Driver_Pack.zip"
    if not archive.exists():
        log.info("Downloading VB-CABLE from %s", VB_CABLE_ZIP)
        urllib.request.urlretrieve(VB_CABLE_ZIP, archive)

    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(destination)

    is_64bit = sys.maxsize > 2**32
    preferred = "VBCABLE_Setup_x64.exe" if is_64bit else "VBCABLE_Setup.exe"
    for name in (preferred, "VBCABLE_Setup_x64.exe", "VBCABLE_Setup.exe"):
        candidate = destination / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError("VB-CABLE setup executable not found in the download")


def open_sound_settings() -> None:
    if is_windows():
        subprocess.Popen(["control", "mmsys.cpl"], shell=True)
