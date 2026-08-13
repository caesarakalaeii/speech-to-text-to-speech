import pytest

from voicemask.text import (
    LocalAgreement,
    clean,
    is_hallucination,
    split_for_speech,
)


@pytest.mark.parametrize(
    "raw, expected",
    [("  hello   world \n", "hello world"), ("", ""), ("a\nb", "a b")],
)
def test_clean_collapses_whitespace(raw, expected):
    assert clean(raw) == expected


@pytest.mark.parametrize(
    "text", ["", "  ", ".", "Thank you.", "thanks for watching!", "[BLANK_AUDIO]", "you"]
)
def test_known_silence_artefacts_are_rejected(text):
    assert is_hallucination(text)


@pytest.mark.parametrize(
    "text", ["Hey chat", "thank you for the sub, that is huge", "I am going to queue up"]
)
def test_real_speech_is_kept(text):
    assert not is_hallucination(text)


class TestSplitForSpeech:
    def test_splits_on_sentence_boundaries(self):
        text = "Welcome back to the stream. That round was close. Let us try again now."
        assert split_for_speech(text) == [
            "Welcome back to the stream.",
            "That round was close.",
            "Let us try again now.",
        ]

    def test_does_not_split_decimals(self):
        assert split_for_speech("I did 3.5 thousand damage that round okay") == [
            "I did 3.5 thousand damage that round okay"
        ]

    def test_short_fragments_are_merged_forward(self):
        # "Oh no." alone would be synthesised with clipped prosody.
        assert split_for_speech("Oh no. That was completely my fault there.") == [
            "Oh no. That was completely my fault there."
        ]

    def test_long_sentence_falls_back_to_clause_boundaries(self):
        text = (
            "I want to say thank you to everyone who showed up tonight, "
            "because this has genuinely been one of the best streams I have had, "
            "and I really did not expect that at all."
        )
        chunks = split_for_speech(text, max_chars=80)
        assert len(chunks) > 1
        assert all(len(c) <= 80 for c in chunks)
        assert " ".join(chunks) == text

    def test_hard_wraps_when_there_is_no_punctuation_at_all(self):
        text = " ".join(["word"] * 100)
        chunks = split_for_speech(text, max_chars=50)
        assert all(len(c) <= 50 for c in chunks)
        assert " ".join(chunks) == text

    def test_empty_input(self):
        assert split_for_speech("   ") == []


class TestLocalAgreement:
    def test_nothing_is_committed_from_a_single_hypothesis(self):
        # One guess is not evidence. Speaking it would speak revised words.
        assert LocalAgreement().insert("hey chat welcome") == ""

    def test_commits_the_prefix_two_runs_agree_on(self):
        la = LocalAgreement()
        la.insert("hey chat welcome")
        # "welcome" survived, "back" is new and still volatile.
        assert la.insert("hey chat welcome back") == "hey chat welcome"

    def test_revised_tail_is_never_spoken(self):
        la = LocalAgreement()
        la.insert("hey chat welcome to the stripe")
        # The recogniser corrects "stripe" -> "stream" once it hears more.
        committed = la.insert("hey chat welcome to the stream")
        assert "stripe" not in committed
        assert committed == "hey chat welcome to the"

    def test_does_not_re_emit_already_committed_words(self):
        la = LocalAgreement()
        la.insert("one two three")
        assert la.insert("one two three four") == "one two three"
        assert la.insert("one two three four five") == "four"

    def test_agreement_ignores_punctuation_and_case_churn(self):
        la = LocalAgreement()
        la.insert("hey chat welcome back")
        # Same words, better punctuation on the second pass: the words agree,
        # so all of them commit, and we emit the better-punctuated spelling.
        assert la.insert("Hey chat, welcome back!") == "Hey chat, welcome back!"

    def test_finalise_emits_the_unspoken_tail(self):
        la = LocalAgreement()
        la.insert("one two three")
        la.insert("one two three four")  # commits "one two three"
        assert la.finalise("one two three four five") == "four five"

    def test_finalise_resets_state_for_the_next_utterance(self):
        la = LocalAgreement()
        la.insert("one two")
        la.insert("one two three")
        la.finalise("one two three")
        assert la.committed == ""
        assert la.insert("brand new sentence") == ""

    def test_full_utterance_is_spoken_exactly_once(self):
        """The property that matters: no dropped words, no repeats."""
        la = LocalAgreement()
        final = "hey chat welcome back to the stream tonight"
        spoken: list[str] = []
        tokens = final.split()
        for i in range(1, len(tokens) + 1):
            spoken.append(la.insert(" ".join(tokens[:i])))
        spoken.append(la.finalise(final))
        assert " ".join(s for s in spoken if s).split() == tokens

    def test_agree_of_three_is_more_conservative(self):
        la = LocalAgreement(agree=3)
        la.insert("one two three")
        assert la.insert("one two three four") == ""
        assert la.insert("one two three four five") == "one two three"

    def test_agree_below_two_is_rejected(self):
        with pytest.raises(ValueError):
            LocalAgreement(agree=1)


class TestSpeechBuffer:
    def test_holds_text_until_a_sentence_closes(self):
        from voicemask.text import SpeechBuffer

        buf = SpeechBuffer()
        assert buf.add("hey chat welcome") == []
        assert buf.add("back to the stream.") == ["hey chat welcome back to the stream."]

    def test_releases_multiple_sentences_at_once(self):
        from voicemask.text import SpeechBuffer

        buf = SpeechBuffer()
        out = buf.add("First one is here. Second one is here too. And a third")
        assert out == ["First one is here. Second one is here too."]
        assert buf.pending == "And a third"

    def test_run_on_speech_is_released_at_a_clause_boundary(self):
        from voicemask.text import SpeechBuffer

        buf = SpeechBuffer(max_chars=60)
        out = buf.add(
            "so I was playing ranked last night, and honestly it went really "
            "badly for me the whole time"
        )
        assert out, "a run-on sentence must not stall playback forever"
        assert out[0].endswith(",")

    def test_flush_returns_everything_left(self):
        from voicemask.text import SpeechBuffer

        buf = SpeechBuffer()
        buf.add("no punctuation here")
        assert buf.flush() == ["no punctuation here"]
        assert buf.pending == ""

    def test_flush_on_empty_buffer(self):
        from voicemask.text import SpeechBuffer

        assert SpeechBuffer().flush() == []

    def test_no_words_are_lost_across_add_and_flush(self):
        from voicemask.text import SpeechBuffer

        buf = SpeechBuffer(max_chars=40)
        source = (
            "okay so the plan for tonight is pretty simple, we are going to "
            "run a few games, then we will do the subathon thing. sound good?"
        )
        spoken = []
        for word in source.split():
            spoken.extend(buf.add(word))
        spoken.extend(buf.flush())
        assert " ".join(spoken).split() == source.split()


class TestVoiceCatalogue:
    def test_every_listed_voice_has_a_unique_display_name(self):
        from voicemask import tts

        displays = [v.display for v in tts.all_voices()]
        assert len(displays) == len(set(displays))

    def test_piper_voices_are_recognised_by_prefix(self):
        from voicemask.tts_piper import PIPER_VOICES, is_piper_voice

        assert all(is_piper_voice(v.id) for v in PIPER_VOICES)
        assert not is_piper_voice("af_heart")

    def test_piper_voice_ids_map_to_huggingface_paths(self):
        from voicemask.tts_piper import _remote_path

        assert _remote_path("en_US-amy-medium") == "en/en_US/amy/medium/en_US-amy-medium"
        assert _remote_path("en_GB-northern_english_male-medium") == (
            "en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium"
        )

    def test_all_catalogue_voices_pass_settings_validation(self):
        from voicemask import tts
        from voicemask.config import Settings

        for voice in tts.all_voices():
            assert Settings(voice=voice.id).validated().voice == voice.id

    def test_an_unknown_voice_falls_back_to_the_default(self):
        from voicemask import tts
        from voicemask.config import Settings

        assert Settings(voice="nope").validated().voice == tts.DEFAULT_VOICE
