"""Run with `python scripts/smoke_test.py`; uses real pinned data and TTS weights.

Kept outside pytest so conftest.py cannot replace dependencies with test doubles.
Requires requirements.txt and network access or a populated Hugging Face cache.
"""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app
import corpus
import kjh_ru_dict
import tts


def main():
    assert app.demo.get_config_file()["components"]
    assert tts.model is None, "Building the app must not load TTS weights"
    for lang, label in (("kjh", "Хакасский"), ("ru", "Русский")):
        word = kjh_ru_dict.lang_words[lang][0]
        result = kjh_ru_dict.find_word_dict(word, label)
        assert result and "Слово не найдено" not in result
    assert corpus.get_connection().execute("SELECT count(*) FROM corpus").fetchone()[0] == len(corpus.ds)
    word, _, examples = corpus.get_random_word_corpus()
    assert word and examples and "Слово не найдено" not in examples
    for speaker in tts.SPEAKER2MODEL_SPEAKER:
        rate, audio = tts.text_to_speech("Пӱӱн чылығ кӱн.", speaker)
        assert rate == tts.SAMPLE_RATE
        assert audio.dtype == np.int16 and audio.ndim == 1
        assert audio.size > 0 and np.any(audio != 0)
        print(f"{speaker}: {audio.size / rate:.2f}s of audio", flush=True)
    print("Real data, app construction and both TTS voices: OK", flush=True)


if __name__ == "__main__":
    main()
