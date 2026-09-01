import pytest

import corpus
from corpus import (
    find_word_corpus,
    format_example,
    get_random_kjh_example,
    get_random_word_corpus,
    prepare_corpus,
)


class TestPrepareCorpus:
    def test_collects_lowercased_words_per_language(self):
        lang2words = prepare_corpus()

        assert set(lang2words) == {"kjh", "ru"}
        assert "книга" in lang2words["kjh"]
        assert "мин" in lang2words["kjh"]
        assert "абакане" in lang2words["ru"]

    def test_skips_punctuation_and_non_alpha_tokens(self):
        lang2words = prepare_corpus()

        for words in lang2words.values():
            assert all(word.isalpha() for word in words)
            assert "." not in words


class TestFormatExample:
    def test_reports_missing_word(self):
        assert format_example([]) == "Нет слова в корпусе"

    def test_joins_examples_with_separator(self):
        assert format_example(["раз", "два"]) == "раз---два"


class TestFindWordCorpus:
    def test_finds_khakas_word_with_translation(self):
        text = find_word_corpus("книга", "Хакасский")

        assert "Ол пала книга хығырча." in text
        assert "Этот ребёнок читает книгу." in text

    def test_finds_russian_word(self):
        text = find_word_corpus("живу", "Русский")

        assert "Мин Ағбанда чуртапчам." in text

    def test_ignores_case_and_spaces(self):
        assert find_word_corpus(" КНИГА ", "Хакасский") == find_word_corpus("книга", "Хакасский")

    def test_language_filter_is_respected(self):
        assert find_word_corpus("живу", "Хакасский") == "Нет слова в корпусе"

    def test_searches_both_languages(self):
        both = find_word_corpus("книга", "Хакасский/Русский")

        assert both.count("---") >= find_word_corpus("книга", "Хакасский").count("---")

    def test_limits_number_of_examples(self):
        text = find_word_corpus("книга", "Хакасский", num_examples=2)

        assert len(text.split("---")) == 2

    def test_does_not_match_part_of_another_word(self):
        assert "Аның книгазы стол ӱстӱнде." not in find_word_corpus("книга", "Хакасский")

    def test_word_at_sentence_edge_is_not_found(self):
        # Известное ограничение: поиск идёт по подстроке ' слово ',
        # поэтому слово в начале или в конце предложения не находится.
        assert find_word_corpus("мин", "Хакасский") == "Нет слова в корпусе"

    def test_reports_unknown_word(self):
        assert find_word_corpus("абырақ", "Хакасский") == "Нет слова в корпусе"

    def test_warns_on_empty_input(self):
        with pytest.warns(UserWarning, match="Введите слово"):
            assert find_word_corpus("   ", "Хакасский") == ""


class TestGetRandomKjhExample:
    def test_respects_max_length(self):
        for _ in range(20):
            assert 0 < len(get_random_kjh_example(30)) <= 30

    def test_returns_sentence_from_corpus(self):
        sentences = {row["kjh"] for row in corpus.ds}

        assert get_random_kjh_example(300) in sentences


class TestGetRandomWordCorpus:
    def test_returns_word_language_and_its_examples(self):
        for _ in range(30):
            word, lang_in, text = get_random_word_corpus()

            assert lang_in in {"Хакасский", "Русский"}
            assert word in corpus.lang2words["kjh" if lang_in == "Хакасский" else "ru"]
            assert text == find_word_corpus(word, lang_in)
