import numpy as np
import pytest

import tts
from tts import MAX_TEXT_LEN, SAMPLE_RATE, random_text_to_speech, text_to_speech


class TestTextToSpeech:
    def test_returns_sample_rate_and_int16_audio(self):
        sample_rate, data = text_to_speech("пӱӱн чылығ кӱн", "Сибдей")

        assert sample_rate == SAMPLE_RATE
        assert data.dtype == np.int16

    def test_passes_normalized_text_and_model_speaker(self):
        tts.model.calls.clear()

        text_to_speech("  Пӱӱн Чылығ Кӱн  ", "Карина")

        assert tts.model.calls[-1] == {
            "text": "пӱӱн чылығ кӱн",
            "speaker": "kjh_karina",
            "sample_rate": SAMPLE_RATE,
        }

    def test_clips_audio_to_int16_range(self):
        _, data = text_to_speech("сӧс", "Сибдей")

        assert data.min() == -32767
        assert data.max() == 32767

    def test_warns_on_empty_text(self):
        with pytest.warns(UserWarning, match="Введите текст"):
            assert text_to_speech("   ", "Сибдей") is None

    def test_warns_on_too_long_text(self):
        with pytest.warns(UserWarning, match=f"> {MAX_TEXT_LEN}"):
            assert text_to_speech("а" * (MAX_TEXT_LEN + 1), "Сибдей") is None

    def test_accepts_text_of_max_length(self):
        assert text_to_speech("а" * MAX_TEXT_LEN, "Сибдей") is not None

    def test_warns_on_unknown_speaker(self):
        with pytest.warns(UserWarning, match="не поддерживается"):
            assert text_to_speech("сӧс", "Незнакомый") is None


class TestRandomTextToSpeech:
    def test_returns_text_speaker_and_audio(self):
        for _ in range(10):
            text, speaker, audio = random_text_to_speech()

            assert speaker in tts.SPEAKER2MODEL_SPEAKER
            assert 0 < len(text) <= MAX_TEXT_LEN
            assert audio is not None
            assert audio[0] == SAMPLE_RATE
