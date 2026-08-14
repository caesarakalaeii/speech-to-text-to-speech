"""Model registry and downloader.

Everything is fetched once, into `paths.models_dir()`, and never again. The
GUI drives this before the first run so the user sees a progress bar instead of
a frozen window on their first sentence.
"""

from __future__ import annotations

import logging
import shutil
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import paths

log = logging.getLogger(__name__)

# Progress reporting: (label, downloaded_bytes, total_bytes_or_None)
ProgressFn = Callable[[str, int, int | None], None]

_KOKORO_RELEASE = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
)


@dataclass(frozen=True)
class Asset:
    name: str
    url: str
    filename: str
    approx_mb: int


# Direct downloads. Hugging Face assets are handled separately because
# huggingface_hub does its own caching and resumption.
ASSETS: dict[str, Asset] = {
    # fp16, not fp32 and emphatically not int8. Measured on an i7-11700K:
    # fp32 RTF 0.19, fp16 RTF 0.17 at half the download, int8 RTF 1.07 -- the
    # quantised build is six times slower because ONNX Runtime inserts
    # dequantise nodes it cannot fuse. See docs/adr/0004.
    "kokoro": Asset(
        name="Kokoro voice model",
        url=_KOKORO_RELEASE + "kokoro-v1.0.fp16.onnx",
        filename="kokoro-v1.0.fp16.onnx",
        approx_mb=178,
    ),
    "kokoro_voices": Asset(
        name="Kokoro voice pack",
        url=_KOKORO_RELEASE + "voices-v1.0.bin",
        filename="voices-v1.0.bin",
        approx_mb=28,
    ),
}

# Silero VAD, as repackaged for onnx-asr. Small enough that the first run
# fetches it without the user noticing.
VAD_REPO = "istupakov/silero-vad-onnx"
VAD_FILE = "silero_vad.onnx"

# The recogniser. v2 is the English-only model: same architecture as the
# multilingual v3 but lower word error rate on English, which is all we need.
STT_MODEL = "nemo-parakeet-tdt-0.6b-v2"
STT_APPROX_MB = 660


def asset_path(key: str) -> Path:
    return paths.models_dir() / ASSETS[key].filename


def is_downloaded(key: str) -> bool:
    path = asset_path(key)
    if not path.exists():
        return False
    # A truncated download is worse than a missing one: it fails later, deep
    # inside ONNX Runtime, with an unreadable error.
    return path.stat().st_size > ASSETS[key].approx_mb * 900_000


def download_asset(key: str, progress: ProgressFn | None = None) -> Path:
    asset = ASSETS[key]
    target = asset_path(key)
    if is_downloaded(key):
        return target

    tmp = target.with_suffix(target.suffix + ".part")
    log.info("Downloading %s from %s", asset.name, asset.url)

    with urllib.request.urlopen(asset.url) as response, tmp.open("wb") as out:
        total = response.length or asset.approx_mb * 1_000_000
        seen = 0
        while chunk := response.read(1 << 18):
            out.write(chunk)
            seen += len(chunk)
            if progress:
                progress(asset.name, seen, total)
    tmp.replace(target)
    return target


def download_vad(progress: ProgressFn | None = None) -> Path:
    from huggingface_hub import hf_hub_download

    if progress:
        progress("Voice activity detector", 0, None)
    cached = hf_hub_download(
        repo_id=VAD_REPO, filename=VAD_FILE, cache_dir=paths.models_dir() / "hf"
    )
    return Path(cached)


def download_stt(progress: ProgressFn | None = None) -> None:
    """Warm the Hugging Face cache for the recogniser.

    onnx-asr resolves the model itself; calling it once here means the first
    real sentence does not pay a 660 MB download.
    """
    import onnx_asr

    if progress:
        progress("Speech recogniser", 0, None)
    onnx_asr.load_model(STT_MODEL)


def all_ready() -> bool:
    return is_downloaded("kokoro") and is_downloaded("kokoro_voices")


def total_download_mb() -> int:
    pending = sum(a.approx_mb for k, a in ASSETS.items() if not is_downloaded(k))
    return pending + STT_APPROX_MB + 2


def free_space_mb(path: Path | None = None) -> int:
    return shutil.disk_usage(path or paths.models_dir()).free // 1_000_000
