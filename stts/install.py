"""Post-install steps: fetch models, make a shortcut, check the virtual mic.

Called once by Install.bat. Everything here is idempotent, so running the
installer twice is harmless.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import models, paths


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _pythonw() -> Path:
    """The windowless interpreter, so the app opens without a console."""
    root = project_root()
    candidate = root / ".venv" / "Scripts" / "pythonw.exe"
    if candidate.exists():
        return candidate
    return Path(sys.executable)


def create_shortcut() -> Path | None:
    """Put a Speech-to-Text-to-Speech shortcut on the desktop. Windows only."""
    if os.name != "nt":
        return None

    desktop = Path(os.path.expanduser("~")) / "Desktop"
    if not desktop.exists():
        return None
    link = desktop / "Speech-to-Text-to-Speech.lnk"

    script = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{link}');"
        "$s.TargetPath = '{target}';"
        "$s.Arguments = '-m stts.cli';"
        "$s.WorkingDirectory = '{cwd}';"
        "$s.Description = 'Speech-to-Text-to-Speech - real-time voice masking';"
        "$s.Save()"
    ).format(link=link, target=_pythonw(), cwd=project_root())

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            check=True,
            capture_output=True,
            timeout=60,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"  Could not create the desktop shortcut ({exc}).")
        print(f"  Start the app with: {project_root() / 'Start.bat'}")
        return None
    return link


def main() -> int:
    print("Speech-to-Text-to-Speech setup")
    print("=" * 46)

    needed = models.total_download_mb()
    free = models.free_space_mb()
    if free < needed + 500:
        print(f"Not enough disk space: need about {needed} MB, {free} MB free.")
        return 1

    print(f"Downloading models (about {needed} MB). This runs once.\n")

    def progress(label: str, done: int, total: int | None) -> None:
        if total:
            filled = done * 30 // total
            bar = "#" * filled + "." * (30 - filled)
            print(f"\r  {label:<22} [{bar}] {done * 100 // total:3d}%", end="", flush=True)
        else:
            print(f"\r  {label:<22} working…", end="", flush=True)

    for key in ("kokoro", "kokoro_voices"):
        models.download_asset(key, progress)
        print()
    models.download_vad(progress)
    print()
    models.download_stt(progress)
    print("\n")

    link = create_shortcut()
    if link:
        print(f"  Desktop shortcut created: {link.name}")

    try:
        from .audio import devices

        if not devices.has_virtual_cable():
            print(
                "\n  Note: no virtual microphone is installed yet.\n"
                "  You need one for OBS or Discord to hear the new voice.\n"
                "  The app will offer to set it up when you first open it."
            )
    except Exception:
        pass

    print(f"\nDone. Settings and logs live in:\n  {paths.data_dir()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
