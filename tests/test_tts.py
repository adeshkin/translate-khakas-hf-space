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
        tts.get_model().calls.clear()

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
        with pytest.warns(UserWarning, match=f"максимум — {MAX_TEXT_LEN}"):
            assert text_to_speech("а" * (MAX_TEXT_LEN + 1), "Сибдей") is None

    def test_accepts_text_of_max_length(self):
        assert text_to_speech("а" * MAX_TEXT_LEN, "Сибдей") is not None

    def test_warns_on_unknown_speaker(self):
        with pytest.warns(UserWarning, match="недоступен"):
            assert text_to_speech("сӧс", "Незнакомый") is None


class TestRandomTextToSpeech:
    def test_returns_text_speaker_and_audio(self):
        for _ in range(10):
            text, speaker, audio = random_text_to_speech()

            assert speaker in tts.SPEAKER2MODEL_SPEAKER
            assert 0 < len(text) <= MAX_TEXT_LEN
            assert audio is not None
            assert audio[0] == SAMPLE_RATE


def test_synthesis_buttons_share_one_queue():
    handlers = [f for f in tts.tts_interface.fns.values()
                if f.fn in (text_to_speech, random_text_to_speech)]
    assert len(handlers) == 2
    assert {f.concurrency_id for f in handlers} == {"tts"}
    assert all(f.concurrency_limit == 1 for f in handlers)


def test_failed_model_load_is_retried_after_cooldown(monkeypatch):
    import gradio as gr

    monkeypatch.setattr(tts, "model", None)
    monkeypatch.setattr(tts, "_retry_after", 0)
    clock = [100.0]
    monkeypatch.setattr(tts, "monotonic", lambda: clock[0])
    calls = []
    download = tts.hf_hub_download

    def fail_download(**kwargs):
        calls.append(kwargs)
        raise OSError("offline")

    monkeypatch.setattr(tts, "hf_hub_download", fail_download)
    for _ in range(2):
        with pytest.raises(gr.Error, match="временно недоступна"):
            text_to_speech("сӧс", "Сибдей")
    assert len(calls) == 1
    assert tts.model is None
    clock[0] += 61
    monkeypatch.setattr(tts, "hf_hub_download", download)
    assert text_to_speech("сӧс", "Сибдей") is not None


def test_invalid_input_does_not_load_model(monkeypatch):
    def unexpected_load():
        pytest.fail("Invalid input must not load the model")

    monkeypatch.setattr(tts, "get_model", unexpected_load)
    with pytest.warns(UserWarning):
        assert text_to_speech("", "Сибдей") is None
