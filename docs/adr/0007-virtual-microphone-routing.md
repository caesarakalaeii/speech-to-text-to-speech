# 7. Virtual microphone routing

Date: 2026-08-13

## Status

Accepted

## Context

The user is a streamer. Playing the masked voice out of a speaker accomplishes
nothing -- OBS, Discord and the browser need it as a **microphone input**.

On Windows that requires a virtual audio cable: a kernel driver exposing a
playback endpoint whose audio reappears on a capture endpoint. We write to
"CABLE Input"; OBS selects "CABLE Output" as its microphone.

v1 ignored this entirely. It played to a chosen output device and left the user
to work out why their stream still had their real voice on it -- which, for
this project's stated purpose, is a privacy failure rather than a papercut.

Options:

1. **Bundle a driver.** Would need code signing, admin rights, and
   redistribution rights we do not have.
2. **Detect and guide.** Detect whether a cable exists; if not, offer to fetch
   the official VB-CABLE installer and hand it over.
3. **Instructions only.** Print a link.
4. **Ignore it.**

## Decision

**Detect, then guide (option 2).**

- `audio/devices.py` recognises VB-CABLE, VB-Audio, Voicemeeter and Virtual
  Audio Cable endpoints by name, and pre-selects a virtual cable as the
  default output when one exists.
- The GUI states plainly which situation the user is in: routed correctly,
  routed to speakers while a cable exists, or no cable installed.
- If none is installed, `windows.guide_virtual_cable_install` explains what
  will happen and where the software comes from, downloads the official
  VB-Audio driver pack, and launches *their* installer with a standard Windows
  elevation prompt.

**The user still approves elevation and still clicks "Install Driver".** We do
not silently install a kernel driver, and the dialog says so. Automating those
clicks would be both hostile and fragile.

Playback fans out to **two** devices: the cable (what chat hears) and an
optional monitor device (what the user hears), each with its own stream and
volume, since they may run at different sample rates.

## Consequences

- Installing the cable needs admin rights and a reboot, once. This is the only
  part of setup that does, and it is unavoidable for a kernel driver.
- On Linux and macOS the GUI points at PipeWire null sinks and BlackHole
  instead; detection by name still works if the device is named conventionally.
- Playing to a real speaker creates an acoustic feedback path: the microphone
  hears the synthesised voice and transcribes it back. `echo_guard` defaults to
  `auto`, enabling suppression only when the output is *not* a virtual cable --
  because in the correct routing there is no feedback path and suppression
  would needlessly deafen the app while it speaks.
- VB-CABLE is donationware and free for personal use. We link and download from
  the vendor rather than redistributing it.
