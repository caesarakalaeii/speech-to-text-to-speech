"""Command line entry point.

`stts` with no arguments opens the GUI -- that is what the desktop
shortcut runs. The subcommands exist for setup, diagnostics and the GPU
benchmark; a normal user never types them.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from . import models, paths, runtime

log = logging.getLogger(__name__)


def _configure_logging(verbose: bool = False) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    try:
        handlers.append(logging.FileHandler(paths.log_path(), encoding="utf-8"))
    except OSError:
        pass
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def cmd_setup(_args: argparse.Namespace) -> int:
    """Download everything so the first real sentence is instant."""
    print(f"Downloading models to {paths.models_dir()}")
    print(f"About {models.total_download_mb()} MB needed, "
          f"{models.free_space_mb()} MB free.\n")

    def progress(label: str, done: int, total: int | None) -> None:
        if total:
            print(f"\r  {label}: {done * 100 // total:3d}%", end="", flush=True)
        else:
            print(f"\r  {label}: working…", end="", flush=True)

    for key in ("kokoro", "kokoro_voices"):
        models.download_asset(key, progress)
        print()
    models.download_vad(progress)
    print()
    models.download_stt(progress)
    print("\nAll models ready.")
    return 0


def cmd_devices(_args: argparse.Namespace) -> int:
    from .audio import devices

    print("Inputs (microphones):")
    for device in devices.input_devices():
        print(f"  [{device.index:3d}] {device.display}")
    print("\nOutputs:")
    for device in devices.output_devices():
        print(f"  [{device.index:3d}] {device.display}")

    cable = devices.virtual_cable_output()
    print(f"\nVirtual microphone: {cable.name if cable else 'not installed'}")
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    from .audio import devices

    print(f"App data           : {paths.data_dir()}")
    print(f"Python             : {sys.version.split()[0]}")
    print(f"Runtime            : {runtime.describe()}")
    print(f"GPU (DirectML)     : {'available' if runtime.has_gpu() else 'not installed'}")
    print(f"Models downloaded  : {'yes' if models.all_ready() else 'no'}")
    print(f"Free disk          : {models.free_space_mb()} MB")
    print(f"Microphones        : {len(devices.input_devices())}")
    print(f"Virtual microphone : {'yes' if devices.has_virtual_cable() else 'no'}")

    try:
        import espeakng_loader

        raw = str(espeakng_loader.get_data_path())
        safe = paths.safe_espeak_data_path(raw)
        note = "ok" if safe == raw else f"staged to {safe} (original path too long)"
        print(f"Pronunciation data : {note}")
    except Exception as exc:
        print(f"Pronunciation data : FAILED ({exc})")
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    """Measure the pipeline end to end. Used by Enable-GPU.bat to decide."""
    import numpy as np

    from .stt import Recogniser
    from .tts import Synthesiser

    use_gpu = args.gpu
    if use_gpu and not runtime.has_gpu():
        print("DirectML is not installed; nothing to benchmark.")
        return 2

    label = "GPU (DirectML)" if use_gpu else "CPU"
    print(f"Benchmarking on {label}…")

    synth = Synthesiser(use_gpu=use_gpu)
    synth.warm_up()
    recog = Recogniser(use_gpu=use_gpu)

    sentences = [
        "Hey chat, welcome back to the stream.",
        "That was a really close round, I almost had it.",
        "Let me know what you want to see next, because I have a few ideas.",
    ]

    tts_ms, stt_ms = [], []
    for sentence in sentences:
        speech = synth.synthesise(sentence, voice="af_heart")
        tts_ms.append(speech.latency_s * 1000)

        audio = speech.audio
        if speech.sample_rate != 16000:
            from .audio.resample import resample

            audio = resample(audio, speech.sample_rate, 16000)
        recog.transcribe(audio[:16000])  # warm up
        result = recog.transcribe(np.asarray(audio, dtype=np.float32))
        stt_ms.append(result.latency_s * 1000)
        print(f"  {speech.duration_s:4.1f}s | speak {tts_ms[-1]:6.0f} ms | "
              f"recognise {stt_ms[-1]:6.0f} ms | {result.text!r}")

    mean_stt = sum(stt_ms) / len(stt_ms)
    mean_tts = sum(tts_ms) / len(tts_ms)
    print(f"\n{label}: recognise {mean_stt:.0f} ms, speak {mean_tts:.0f} ms, "
          f"total {mean_stt + mean_tts:.0f} ms")
    return 0


def cmd_run(_args: argparse.Namespace) -> int:
    from .gui import main as gui_main

    gui_main()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stts", description="Real-time local voice masking."
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("setup", help="download the models").set_defaults(func=cmd_setup)
    sub.add_parser("devices", help="list audio devices").set_defaults(func=cmd_devices)
    sub.add_parser("doctor", help="check the installation").set_defaults(func=cmd_doctor)
    bench = sub.add_parser("bench", help="measure latency")
    bench.add_argument("--gpu", action="store_true", help="use DirectML instead of CPU")
    bench.set_defaults(func=cmd_bench)

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    handler = getattr(args, "func", cmd_run)
    started = time.perf_counter()
    try:
        return handler(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        log.exception("stts failed after %.1fs", time.perf_counter() - started)
        print(f"\nError: {exc}\nDetails: {paths.log_path()}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
