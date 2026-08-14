"""Text post-processing between the recogniser and the synthesiser.

Two jobs live here, both pure functions of their input so they can be tested
without loading a model:

* cleaning up recogniser output (silence hallucinations, whitespace)
* deciding *when* a piece of text is safe to speak, which is what actually
  buys us low latency -- see :class:`LocalAgreement`.
"""

from __future__ import annotations

import re

# Recognisers trained on scraped video reliably emit these on silence, breath
# or keyboard noise. Speaking them would be worse than saying nothing.
HALLUCINATIONS = frozenset(
    {
        "",
        ".",
        "you",
        "bye",
        "bye.",
        "thank you",
        "thank you.",
        "thanks for watching",
        "thanks for watching!",
        "thanks for watching.",
        "please subscribe",
        "subscribe",
        "like and subscribe",
        "[music]",
        "(music)",
        "[silence]",
        "[blank_audio]",
        "uh",
        "um",
        "mm",
        "hmm",
    }
)

_WS = re.compile(r"\s+")
_WORD = re.compile(r"[^\W_]+", re.UNICODE)
# Split after . ? ! : ; and after a comma, but only when a space follows, so
# decimals ("3.5") and abbreviations glued to the next char stay intact.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_CLAUSE_END = re.compile(r"(?<=[,;:])\s+")


def clean(text: str) -> str:
    """Collapse whitespace and strip surrounding noise."""
    return _WS.sub(" ", (text or "").replace("\n", " ")).strip()


def is_hallucination(text: str) -> bool:
    """True if `text` is a known silence artefact and must not be spoken."""
    stripped = clean(text).lower().strip(" .!?,")
    if not stripped:
        return True
    return stripped in HALLUCINATIONS or clean(text).lower() in HALLUCINATIONS


def normalise_word(word: str) -> str:
    """Comparison key for agreement: case- and punctuation-insensitive."""
    return "".join(_WORD.findall(word.lower()))


def words(text: str) -> list[str]:
    return [w for w in clean(text).split(" ") if w]


def split_for_speech(text: str, max_chars: int = 180, min_chars: int = 12) -> list[str]:
    """Split `text` into chunks that are worth handing to the synthesiser.

    Synthesising sentence by sentence lets playback of chunk N overlap
    generation of chunk N+1, so the listener hears the first words long before
    the whole reply exists. Chunks shorter than `min_chars` are merged forward,
    because very short fragments make the synthesiser clip prosody.
    """
    text = clean(text)
    if not text:
        return []

    chunks: list[str] = []
    for sentence in _SENTENCE_END.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        # A single sentence longer than max_chars would stall playback, so fall
        # back to clause boundaries, then to a hard word-count split.
        if len(sentence) <= max_chars:
            chunks.append(sentence)
            continue
        for clause in _split_long(sentence, max_chars):
            chunks.append(clause)

    merged: list[str] = []
    for chunk in chunks:
        if merged and len(merged[-1]) < min_chars:
            merged[-1] = f"{merged[-1]} {chunk}"
        else:
            merged.append(chunk)
    return merged


def _split_long(sentence: str, max_chars: int) -> list[str]:
    parts: list[str] = []
    buf = ""
    for clause in _CLAUSE_END.split(sentence):
        candidate = f"{buf} {clause}".strip()
        if buf and len(candidate) > max_chars:
            parts.append(buf)
            buf = clause
        else:
            buf = candidate
    if buf:
        parts.append(buf)

    out: list[str] = []
    for part in parts:
        while len(part) > max_chars:
            cut = part.rfind(" ", 0, max_chars)
            if cut <= 0:
                cut = max_chars
            out.append(part[:cut].strip())
            part = part[cut:].strip()
        if part:
            out.append(part)
    return out


class LocalAgreement:
    """Commit only the part of a growing transcript that has stopped changing.

    While someone is still talking we re-run the recogniser on the audio so
    far, every few hundred milliseconds. Each run returns a slightly different
    guess, and the tail of that guess is the volatile part -- the recogniser
    revises it once it hears the next word. Speaking the tail immediately would
    mean speaking words the user never said.

    The fix (LocalAgreement-n, from the whisper-streaming literature) is to
    only speak the prefix that `n` consecutive runs agreed on. That prefix is
    stable in practice, so we can start synthesising it while the user is still
    mid-sentence instead of waiting for them to stop.
    """

    def __init__(self, agree: int = 2) -> None:
        if agree < 2:
            raise ValueError("agree must be >= 2")
        self._agree = agree
        self._history: list[list[str]] = []
        self._committed: list[str] = []

    @property
    def committed(self) -> str:
        return " ".join(self._committed)

    def reset(self) -> None:
        self._history.clear()
        self._committed.clear()

    def insert(self, hypothesis: str) -> str:
        """Feed the latest full-utterance guess; return newly safe-to-speak text."""
        current = words(hypothesis)
        self._history.append(current)
        if len(self._history) > self._agree:
            self._history.pop(0)

        if len(self._history) < self._agree:
            return ""

        stable = self._history[0]
        for other in self._history[1:]:
            stable = _common_prefix(stable, other)

        if len(stable) <= len(self._committed):
            return ""

        # Use the newest spelling of the agreed words -- later runs punctuate
        # and capitalise better once they have more right-hand context.
        new = current[len(self._committed) : len(stable)]
        self._committed = current[: len(stable)]
        return " ".join(new)

    def finalise(self, hypothesis: str) -> str:
        """Utterance is over: return whatever has not been spoken yet."""
        current = words(hypothesis)
        prefix = len(_common_prefix(current, self._committed))
        # If the final pass revised words we already spoke there is nothing we
        # can do about it -- they are out. Only emit the genuinely new tail.
        tail = current[max(prefix, len(self._committed)) :]
        self.reset()
        return " ".join(tail)


class SpeechBuffer:
    """Accumulate committed words and release them in speakable chunks.

    :class:`LocalAgreement` hands us a few words at a time, but handing a few
    words at a time to the synthesiser produces choppy, wrongly-stressed
    speech. So we buffer until a sentence closes, then release. If the speaker
    never punctuates -- a run-on stream of consciousness, which is exactly how
    people talk on stream -- we release at a clause boundary once the buffer
    passes `max_chars`, so playback never stalls waiting for a full stop.
    """

    def __init__(self, max_chars: int = 140, min_chars: int = 12) -> None:
        self._max = max_chars
        self._min = min_chars
        self._buffer = ""

    @property
    def pending(self) -> str:
        return self._buffer

    def add(self, new_text: str) -> list[str]:
        self._buffer = clean(f"{self._buffer} {new_text}")
        chunks: list[str] = []
        while True:
            chunk = self._take()
            if chunk is None:
                break
            chunks.append(chunk)
        return chunks

    def flush(self) -> list[str]:
        remaining = clean(self._buffer)
        self._buffer = ""
        return split_for_speech(remaining, self._max, self._min) if remaining else []

    def _take(self) -> str | None:
        match = None
        for candidate in _SENTENCE_END.finditer(self._buffer):
            match = candidate
        if match is not None:
            head = self._buffer[: match.start()].strip()
            if len(head) >= self._min:
                self._buffer = self._buffer[match.end() :]
                return head
            return None

        # A sentence that ends exactly at the end of the buffer has no
        # trailing whitespace to match on, but it is still finished and
        # holding it back would add a whole endpoint delay to every sentence.
        if _ends_sentence(self._buffer) and len(self._buffer) >= self._min:
            head, self._buffer = self._buffer.strip(), ""
            return head

        if len(self._buffer) <= self._max:
            return None

        # No sentence end in sight and the buffer is long enough that waiting
        # would be audible. Cut at the latest clause or word boundary.
        window = self._buffer[: self._max]
        cut = max(window.rfind(", "), window.rfind("; "), window.rfind(": "))
        if cut <= self._min:
            cut = window.rfind(" ")
        if cut <= 0:
            return None
        head = self._buffer[: cut + 1].strip()
        self._buffer = self._buffer[cut + 1 :].lstrip()
        return head


def _ends_sentence(buffer: str) -> bool:
    """True if `buffer` ends on terminal punctuation rather than a decimal."""
    stripped = buffer.rstrip()
    if not stripped or stripped[-1] not in ".!?":
        return False
    # "I did 3." is almost certainly "3.5" mid-arrival, not a finished sentence.
    return not (stripped[-1] == "." and len(stripped) >= 2 and stripped[-2].isdigit())


def _common_prefix(a: list[str], b: list[str]) -> list[str]:
    n = 0
    limit = min(len(a), len(b))
    while n < limit and normalise_word(a[n]) == normalise_word(b[n]):
        n += 1
    return a[:n]
