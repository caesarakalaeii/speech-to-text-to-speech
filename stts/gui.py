"""Tkinter front end.

Tkinter because it ships with Python: adding a GUI toolkit to the dependency
list would mean another wheel to download and another thing to go wrong on a
machine whose owner did not ask to be a developer.

Everything slow -- loading models, downloading them, synthesising a preview --
happens on a worker thread. Tk is not thread-safe, so worker threads never
touch a widget; they push onto a queue that the UI polls.
"""

from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from . import models, pipeline, runtime, tts, windows
from .audio import devices
from .config import Settings
from .paths import log_path

log = logging.getLogger(__name__)

PAD = 12


class App:
    def __init__(self) -> None:
        self.settings = Settings.load().validated()
        self.pipeline: pipeline.Pipeline | None = None
        self._events: queue.Queue = queue.Queue()
        self._busy = False
        self._synth_for_preview: tts.VoiceRouter | None = None

        self.root = tk.Tk()
        self.root.title("Speech-to-Text-to-Speech")
        self.root.minsize(640, 620)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()
        self._refresh_devices()
        self.root.after(50, self._drain_events)

    # -- layout ------------------------------------------------------------
    def _build(self) -> None:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("Warn.TLabel", foreground="#b34700")
        style.configure("Good.TLabel", foreground="#1a7f37")
        style.configure("Dim.TLabel", foreground="#666666")

        outer = ttk.Frame(self.root, padding=PAD)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)

        # -- start/stop + status
        header = ttk.Frame(outer)
        header.pack(fill=tk.X)
        self.start_button = ttk.Button(
            header, text="Start", style="Big.TButton", command=self._toggle
        )
        self.start_button.pack(side=tk.LEFT)
        self.status = ttk.Label(header, text="Ready", font=("Segoe UI", 10))
        self.status.pack(side=tk.LEFT, padx=PAD)

        self.level = ttk.Progressbar(header, maximum=1.0, length=140)
        self.level.pack(side=tk.RIGHT)
        ttk.Label(header, text="Mic ").pack(side=tk.RIGHT)

        # -- audio routing
        audio = ttk.LabelFrame(outer, text="Audio", padding=PAD)
        audio.pack(fill=tk.X, pady=(PAD, 0))
        audio.columnconfigure(1, weight=1)

        self.input_box = self._combo(audio, 0, "Microphone")
        self.output_box = self._combo(audio, 1, "Voice goes to")
        self.monitor_box = self._combo(audio, 2, "Also hear it on")

        self.routing_hint = ttk.Label(audio, text="", style="Dim.TLabel", wraplength=560)
        self.routing_hint.grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self.cable_button = ttk.Button(
            audio, text="Set up virtual microphone…", command=self._install_cable
        )
        self.cable_button.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # -- voice
        voice = ttk.LabelFrame(outer, text="Voice", padding=PAD)
        voice.pack(fill=tk.X, pady=(PAD, 0))
        voice.columnconfigure(1, weight=1)

        ttk.Label(voice, text="Voice").grid(row=0, column=0, sticky="w")
        self.voice_box = ttk.Combobox(voice, state="readonly", width=44)
        self._voices = tts.all_voices()
        self.voice_box["values"] = [v.display for v in self._voices]
        self.voice_box.grid(row=0, column=1, sticky="ew", padx=(PAD, 6))
        self.voice_box.bind("<<ComboboxSelected>>", self._on_voice_change)
        current = next((v for v in self._voices if v.id == self.settings.voice), self._voices[0])
        self.voice_box.set(current.display)
        ttk.Button(voice, text="Preview", command=self._preview).grid(row=0, column=2)

        self.speed = self._slider(voice, 1, "Speed", 0.7, 1.4, self.settings.speed, "{:.2f}x")
        self.delay = self._slider(
            voice, 2, "Response delay", 200, 800, self.settings.endpoint_ms, "{:.0f} ms"
        )
        ttk.Label(
            voice,
            text="Lower delay responds faster but may cut you off mid-sentence.",
            style="Dim.TLabel",
        ).grid(row=3, column=0, columnspan=3, sticky="w")

        # -- transcript
        live = ttk.LabelFrame(outer, text="Live", padding=PAD)
        live.pack(fill=tk.BOTH, expand=True, pady=(PAD, 0))
        self.transcript = tk.Text(live, height=8, wrap="word", state="disabled",
                                  font=("Segoe UI", 10), relief="flat", background="#fbfbfb")
        self.transcript.pack(fill=tk.BOTH, expand=True)
        self.transcript.tag_configure("heard", foreground="#555555")
        self.transcript.tag_configure("spoke", foreground="#0b5cad")

        self.metrics = ttk.Label(outer, text="", style="Dim.TLabel")
        self.metrics.pack(fill=tk.X, pady=(6, 0))

    def _combo(self, parent: ttk.Frame, row: int, label: str) -> ttk.Combobox:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        box = ttk.Combobox(parent, state="readonly", width=52)
        box.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(PAD, 0), pady=3)
        box.bind("<<ComboboxSelected>>", lambda _event: self._on_device_change())
        return box

    def _slider(
        self, parent: ttk.Frame, row: int, label: str, low: float, high: float,
        initial: float, fmt: str,
    ) -> tk.DoubleVar:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        var = tk.DoubleVar(value=initial)
        readout = ttk.Label(parent, text=fmt.format(initial), width=8)
        scale = ttk.Scale(
            parent, from_=low, to=high, variable=var, orient=tk.HORIZONTAL,
            command=lambda _v: readout.configure(text=fmt.format(var.get())),
        )
        scale.grid(row=row, column=1, sticky="ew", padx=(PAD, 6), pady=3)
        readout.grid(row=row, column=2, sticky="w")
        return var

    # -- device handling ---------------------------------------------------
    def _refresh_devices(self) -> None:
        self._inputs = devices.input_devices()
        self._outputs = devices.output_devices()

        self.input_box["values"] = [d.display for d in self._inputs]
        self.output_box["values"] = [d.display for d in self._outputs]
        self.monitor_box["values"] = ["(none)"] + [d.display for d in self._outputs]

        self._select(self.input_box, self._inputs, self.settings.input_device,
                     devices.default_input())
        cable = devices.virtual_cable_output()
        self._select(self.output_box, self._outputs, self.settings.output_device,
                     cable or devices.default_output())
        if self.settings.monitor_device:
            self._select(self.monitor_box, self._outputs, self.settings.monitor_device, None)
        else:
            self.monitor_box.set("(none)")
        self._on_device_change()

    @staticmethod
    def _select(box: ttk.Combobox, pool: list[devices.Device], stored: str | None,
                fallback: devices.Device | None) -> None:
        chosen = devices.find_by_name(stored, pool[0].is_input if pool else True) if stored else None
        chosen = chosen or fallback
        if chosen is not None:
            box.set(chosen.display)
        elif pool:
            box.set(pool[0].display)

    def _device_from(self, box: ttk.Combobox, pool: list[devices.Device]) -> devices.Device | None:
        value = box.get()
        if not value or value == "(none)":
            return None
        for device in pool:
            if device.display == value:
                return device
        return None

    def _on_device_change(self) -> None:
        output = self._device_from(self.output_box, self._outputs)
        if output is not None and output.is_virtual_cable:
            self.routing_hint.configure(
                text=f"Good — in OBS or Discord pick the matching “CABLE Output” as "
                     f"your microphone. Chat will hear only the new voice.",
                style="Good.TLabel",
            )
            self.cable_button.grid_remove()
        elif devices.has_virtual_cable():
            self.routing_hint.configure(
                text="This plays out of your speakers. To send the new voice to OBS or "
                     "Discord, pick the “CABLE Input” device above.",
                style="Warn.TLabel",
            )
            self.cable_button.grid_remove()
        else:
            self.routing_hint.configure(
                text="No virtual microphone found. Without one, apps still hear your real "
                     "voice. Set one up to route the new voice into OBS or Discord.",
                style="Warn.TLabel",
            )
            self.cable_button.grid()

    # -- actions -----------------------------------------------------------
    def _on_voice_change(self, _event=None) -> None:
        for voice in self._voices:
            if voice.display == self.voice_box.get():
                self.settings.voice = voice.id
                if self.pipeline is not None:
                    self.pipeline.settings.voice = voice.id
                return

    def _preview(self) -> None:
        self._on_voice_change()
        self._run_async("Loading voice…", self._do_preview)

    def _do_preview(self, report: Callable[[str], None]) -> None:
        if self._synth_for_preview is None:
            if not models.all_ready():
                self._download(report)
            self._synth_for_preview = tts.VoiceRouter(use_gpu=self.settings.use_gpu)
        report("Speaking preview…")
        speech = self._synth_for_preview.synthesise(
            "This is how you will sound to your chat.",
            voice=self.settings.voice,
            speed=self.speed.get(),
        )
        from .audio.playback import Player

        monitor = self._device_from(self.monitor_box, self._outputs)
        player = Player(self._device_from(self.output_box, self._outputs), monitor,
                        self.settings.volume, self.settings.monitor_volume)
        player.start()
        player.play(speech.audio, speech.sample_rate)
        threading.Event().wait(speech.duration_s + 0.4)
        player.stop()
        report("Ready")

    def _install_cable(self) -> None:
        windows.guide_virtual_cable_install(self.root)
        self._refresh_devices()

    def _toggle(self) -> None:
        if self.pipeline is not None and self.pipeline.running:
            self._stop()
        else:
            self._start()

    def _start(self) -> None:
        self._capture_settings()
        self.settings.save()
        self._run_async("Loading models…", self._do_start)

    def _do_start(self, report: Callable[[str], None]) -> None:
        from .audio.capture import MicCapture
        from .audio.playback import Player
        from .stt import Recogniser
        from .vad import SileroVad

        if not models.all_ready():
            self._download(report)

        report("Loading voice detector…")
        vad = SileroVad(models.download_vad())
        report("Loading recogniser… (first time takes a minute)")
        recogniser = Recogniser(use_gpu=self.settings.use_gpu)
        report("Loading voice…")
        synthesiser = tts.VoiceRouter(use_gpu=self.settings.use_gpu)
        synthesiser.warm_up(self.settings.voice)
        self._synth_for_preview = synthesiser

        output = self._device_from(self.output_box, self._outputs)
        monitor = self._device_from(self.monitor_box, self._outputs)
        echo_guard = {
            "on": True,
            "off": False,
        }.get(self.settings.echo_guard, output is None or not output.is_virtual_cable)

        self.pipeline = pipeline.Pipeline(
            settings=self.settings,
            recogniser=recogniser,
            synthesiser=synthesiser,
            vad=vad,
            capture=MicCapture(self._device_from(self.input_box, self._inputs),
                               gain=self.settings.mic_gain),
            player=Player(output, monitor, self.settings.volume,
                          self.settings.monitor_volume),
            on_event=self._events.put,
            echo_guard=echo_guard,
        )
        self.pipeline.start()
        self._events.put(("__started__",))

    def _download(self, report: Callable[[str], None]) -> None:
        def progress(label: str, done: int, total: int | None) -> None:
            if total:
                report(f"Downloading {label}… {done * 100 // total}%")
            else:
                report(f"Downloading {label}…")

        for key in ("kokoro", "kokoro_voices"):
            models.download_asset(key, progress)
        models.download_vad(progress)
        models.download_stt(progress)

    def _stop(self) -> None:
        if self.pipeline is not None:
            self.pipeline.stop()
            self.pipeline = None
        self.start_button.configure(text="Start", state="normal")
        self.status.configure(text="Stopped")
        self._set_inputs_enabled(True)

    def _capture_settings(self) -> None:
        self._on_voice_change()
        inp = self._device_from(self.input_box, self._inputs)
        out = self._device_from(self.output_box, self._outputs)
        mon = self._device_from(self.monitor_box, self._outputs)
        self.settings.input_device = inp.name if inp else None
        self.settings.output_device = out.name if out else None
        self.settings.monitor_device = mon.name if mon else None
        self.settings.speed = round(self.speed.get(), 2)
        self.settings.endpoint_ms = int(self.delay.get())
        self.settings.validated()

    # -- async plumbing ----------------------------------------------------
    def _run_async(self, initial: str, work: Callable[[Callable[[str], None]], None]) -> None:
        if self._busy:
            return
        self._busy = True
        self._set_inputs_enabled(False)
        self.start_button.configure(state="disabled")
        self.status.configure(text=initial)

        def report(message: str) -> None:
            self._events.put(("__status__", message))

        def runner() -> None:
            try:
                work(report)
            except Exception as exc:  # surfaced in the UI, logged in full
                log.exception("Background task failed")
                self._events.put(("__error__", str(exc)))
            finally:
                self._events.put(("__done__",))

        threading.Thread(target=runner, daemon=True).start()

    def _set_inputs_enabled(self, enabled: bool) -> None:
        """Lock the device pickers while running or loading.

        The start/stop button is deliberately not touched here: it stays
        usable while the pipeline runs, otherwise there would be no way to
        stop it.
        """
        state = "readonly" if enabled else "disabled"
        for box in (self.input_box, self.output_box, self.monitor_box):
            box.configure(state=state)

    def _drain_events(self) -> None:
        try:
            while True:
                event = self._events.get_nowait()
                self._handle(event)
        except queue.Empty:
            pass
        if self.pipeline is not None and self.pipeline.running:
            stats = self.pipeline.stats
            self.metrics.configure(
                text=f"delay {stats.response_ms:.0f} ms   ·   recognise "
                     f"{stats.stt_ms:.0f} ms   ·   speak {stats.tts_ms:.0f} ms"
                     f"   ·   {stats.utterances} phrases"
            )
        self.root.after(50, self._drain_events)

    def _handle(self, event) -> None:
        if isinstance(event, tuple):
            kind = event[0]
            if kind == "__status__":
                self.status.configure(text=event[1])
            elif kind == "__error__":
                self.status.configure(text="Something went wrong")
                messagebox.showerror(
                    "Speech-to-Text-to-Speech",
                    f"{event[1]}\n\nDetails were written to:\n{log_path()}",
                )
            elif kind == "__done__":
                self._busy = False
                self.start_button.configure(state="normal")
                self._set_inputs_enabled(self.pipeline is None or not self.pipeline.running)
            elif kind == "__started__":
                self.start_button.configure(text="Stop", state="normal")
                self.status.configure(text="Listening")
                self._set_inputs_enabled(False)
            return

        if isinstance(event, pipeline.Status):
            self.status.configure(text=event.message)
        elif isinstance(event, pipeline.Level):
            self.level["value"] = min(1.0, event.rms * 12)
        elif isinstance(event, pipeline.Heard):
            self._append(f"{event.text} ", "heard")
        elif isinstance(event, pipeline.Spoke):
            self._append(f"\n🔊 {event.text}\n", "spoke")
        elif isinstance(event, pipeline.Failed):
            self.status.configure(text=event.message)

    def _append(self, text: str, tag: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert(tk.END, text, tag)
        # Keep the widget from growing without bound over a long stream.
        if float(self.transcript.index(tk.END)) > 400:
            self.transcript.delete("1.0", "200.0")
        self.transcript.see(tk.END)
        self.transcript.configure(state="disabled")

    def _on_close(self) -> None:
        self._capture_settings()
        self.settings.save()
        self._stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    log.info("Starting GUI (%s)", runtime.describe())
    App().run()
