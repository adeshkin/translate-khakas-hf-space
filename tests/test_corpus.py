import os

import pytest

import corpus
from corpus import (
    build_index,
    find_word_corpus,
    format_example,
    get_random_kjh_example,
    get_random_word_corpus,
    quote_phrase,
)


class TestBuildIndex:
    def test_indexes_every_pair(self):
        rows = corpus.get_connection().execute('SELECT count(*) FROM corpus').fetchone()

        assert rows[0] == len(corpus.ds)

    def test_rowids_are_contiguous(self):
        # случайный пример выбирается обращением к rowid напрямую
        bounds = corpus.get_connection().execute(
            'SELECT min(rowid), max(rowid) FROM corpus').fetchone()

        assert bounds == (1, len(corpus.ds))

    def test_reuses_prepared_database(self):
        assert os.path.exists(corpus.db_path)
        assert build_index() == corpus.db_path


class TestQuotePhrase:
    def test_wraps_word_in_quotes(self):
        assert quote_phrase("книга") == '"книга"'

    def test_escapes_quotes_in_input(self):
        assert quote_phrase('кни"га') == '"кни""га"'


class TestFormatExample:
    def test_reports_missing_word(self):
        assert format_example([]) == "Нет слова в корпусе"

    def test_joins_examples_with_separator(self):
        assert format_example(["раз", "два"]) == "раз\n\n---\n\nдва"


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

        assert both.count("---") > find_word_corpus("книга", "Хакасский").count("---")

    def test_limits_number_of_examples(self):
        text = find_word_corpus("книга", "Хакасский", num_examples=2)

        assert len(text.split("---")) == 2

    def test_does_not_match_part_of_another_word(self):
        assert "Аның книгазы стол ӱстӱнде." not in find_word_corpus("книга", "Хакасский")

    def test_finds_word_at_sentence_start(self):
        assert "Мин Ағбанда чуртапчам." in find_word_corpus("мин", "Хакасский")

    def test_finds_word_before_punctuation(self):
        assert "Мин Ағбанда чуртапчам." in find_word_corpus("чуртапчам", "Хакасский")

    def test_falls_back_to_prefix_search(self):
        text = find_word_corpus("книгаз", "Хакасский")

        assert "Точных совпадений нет" in text
        assert "Аның книгазы стол ӱстӱнде." in text

    def test_exact_match_wins_over_prefix(self):
        assert "Точных совпадений нет" not in find_word_corpus("книга", "Хакасский")

    def test_reports_unknown_word(self):
        assert find_word_corpus("абырақ", "Хакасский") == "Нет слова в корпусе"

    @pytest.mark.parametrize("word", ['кни"га', "AND OR", "*", "...", "123"])
    def test_survives_query_syntax_in_input(self, word):
        assert find_word_corpus(word, "Хакасский/Русский") == "Нет слова в корпусе"

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
            assert text == find_word_corpus(word, lang_in)
            # слово взято из самого корпуса, поэтому пример обязан найтись точно
            assert text != "Нет слова в корпусе"
            assert "Точных совпадений нет" not in text
