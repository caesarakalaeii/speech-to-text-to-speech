"""Where Speech-to-Text-to-Speech keeps its models, settings and logs.

Also home to the espeak-ng path guard, which exists for a genuinely obscure
reason: espeak-ng copies the data directory path into a fixed 160-byte buffer.
Point it at a longer path and it silently truncates, fails to find `phontab`,
and aborts the process with a confusing error. Python's site-packages path on
Windows plus a deep install directory gets there easily -- e.g. installing into
a OneDrive-synced Downloads folder. So we measure the path and, when it is too
long, stage a copy of the data somewhere short.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

APP_NAME = "stts"

# espeak-ng's PATH_HOME buffer is 160 bytes. It appends "/espeak-ng-data"
# (15) and then filenames such as "/phondata-manifest" (19) on top, so the
# directory we hand it must stay well under that or it is silently truncated.
_ESPEAK_PATH_LIMIT = 160 - 15 - 25


def data_dir() -> Path:
    """Per-user application directory (models, settings, logs)."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def models_dir() -> Path:
    path = data_dir() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return data_dir() / "settings.json"


def log_path() -> Path:
    return data_dir() / "stts.log"


def safe_espeak_data_path(raw_path: str | Path, staging: Path | None = None) -> str:
    """Return an espeak-ng data path short enough for espeak's path buffer.

    If `raw_path` is already short, it is returned unchanged. Otherwise the
    directory is copied once into `staging` (default: the app data dir) and the
    copy is returned. Copying ~12 MB once beats an unexplainable crash.
    """
    raw_path = Path(raw_path)
    if len(str(raw_path)) <= _ESPEAK_PATH_LIMIT:
        return str(raw_path)

    staging = staging or data_dir()
    target = staging / "espeak-ng-data"
    if len(str(target)) > _ESPEAK_PATH_LIMIT:
        # Even the app dir is too deep (very unusual). Fall back to the
        # filesystem root, which is always short enough.
        root = Path("C:/stts") if os.name == "nt" else Path("/tmp/stts")
        root.mkdir(parents=True, exist_ok=True)
        target = root / "espeak-ng-data"

    if not (target / "phontab").exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(raw_path, target, dirs_exist_ok=True)
    return str(target)
