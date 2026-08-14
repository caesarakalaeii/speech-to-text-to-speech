# 6. One-click Windows install via uv

Date: 2026-08-13

## Status

Accepted

## Context

The user is not technical and the install should be as close to one click as
possible.

v1 offered three install paths across five documents. The "easiest" one told
the user to right-click `setup.bat`, run it as Administrator, wait 20-30
minutes while it installed Python, FFmpeg, CUDA and espeak-ng system-wide,
then hand-edit a `.env` file before running the app. It also required Python to
already be on `PATH` for the non-admin path -- which, for someone who has
never installed Python, it is not.

Requirements for v2:

- No pre-installed Python.
- No administrator rights (a driver install is the one exception, ADR 7).
- No hand-edited config files.
- Nothing installed system-wide that could break other software.

## Decision

**`uv` bootstraps everything**, driven by a 36-line `Install.bat`:

1. If `uv` is missing, fetch it with the official Astral install script. It is
   a single static binary and installs to `%USERPROFILE%\.local\bin` -- no
   admin rights.
2. `uv sync --no-dev` reads `pyproject.toml`, **downloads a private CPython
   3.12** if the machine has none, creates `.venv`, and installs the
   dependencies. The user never sees Python.
3. `uv run python -m stts.install` downloads the models with a progress
   bar and creates a desktop shortcut pointing at `pythonw.exe`, so the app
   opens with no console window.

Configuration lives in `%LOCALAPPDATA%\stts\settings.json`, written by the
GUI. There is no `.env` to edit.

The batch files stay thin -- the longest is 36 lines -- because batch is a poor
language for logic. Anything conditional lives in Python.

### The espeak-ng path-length trap

espeak-ng copies its data directory path into a fixed 160-byte buffer. Exceed
it and the path is silently truncated, `phontab` is not found, and the process
**aborts** with an error naming a path from the machine where the wheel was
built -- which is deeply confusing.

This is easy to hit on Windows: `<install dir>\.venv\Lib\site-packages\
espeakng_loader\espeak-ng-data` is ~55 characters before the install directory
is counted, and a user who extracts a ZIP into a OneDrive-synced Downloads
folder starts ~90 characters in. It was hit during development, and diagnosed
only by bisecting path lengths.

`paths.safe_espeak_data_path` measures the path and, if it is over 120
characters, copies the data once somewhere short. `stts doctor` reports
which path is in use.

## Consequences

- Install is: download the ZIP, extract, double-click `Install.bat`, wait.
  Then a desktop shortcut.
- ~120 MB of wheels plus ~870 MB of models, downloaded once.
- `uv.lock` is committed, so every install resolves to identical versions.
- We depend on `astral.sh` being reachable at install time. The alternative --
  vendoring `uv` -- would mean committing a 30 MB binary and hand-updating it.
- `Report-Problem.bat` writes `stts doctor` output plus the log to the
  desktop, so a support request is one file rather than a conversation.
