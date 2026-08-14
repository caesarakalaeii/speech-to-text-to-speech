# 1. Record architecture decisions

Date: 2026-08-13

## Status

Accepted

## Context

Version 1 of this project accumulated six interchangeable backends (OpenAI
Whisper, NVIDIA NeMo Parakeet, Speaker.bot, NeuTTS Air, Piper, StyleTTS2),
five `requirements-*.txt` files and eight setup documents, with no record of
why any of them were chosen. Two of the backends could not run on the target
machine at all. Nobody could tell which combination was supposed to be used,
because nothing had ever been measured.

The v2 rewrite makes a small number of choices that are load-bearing: a single
inference runtime, one recogniser, one synthesiser, and a latency design that
the rest of the code is shaped around. Those need to be written down with the
measurements that justify them, so the next person can tell a considered
decision from an accident.

## Decision

We record architecturally significant decisions as ADRs in `docs/adr/`, in the
format described by Michael Nygard.

Each ADR states the constraint it is solving for, the options considered, and
where possible the measurement that settled it. An ADR is superseded rather
than edited, so the reasoning at the time stays legible.

## Consequences

Changing the inference runtime, either model, the latency strategy or the
install mechanism requires a new ADR. Ordinary changes -- tuning a default,
adding a voice, fixing a bug -- do not.

The measurements quoted in these ADRs were taken on an Intel i7-11700K, which
is slower than the target machine (Ryzen 7 7800X3D). They are therefore
conservative: the deployed system should be faster than the numbers recorded
here, and any regression below them is a real regression.
