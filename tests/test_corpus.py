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
        assert format_example([]) == "Слово не найдено в корпусе"

    def test_joins_examples_with_separator(self):
        assert format_example(["раз", "два"]) == "раз\n\n---\n\nдва"


def example_set(text):
    """Порядок примеров случайный, поэтому сравниваем подборки как множества."""
    return {part.strip() for part in text.split("---")}


class TestFindWordCorpus:
    def test_finds_khakas_word_with_translation(self):
        text = find_word_corpus("книга", "Хакасский")

        assert "Ол пала <b>книга</b> хығырча." in text
        assert "Этот ребёнок читает книгу." in text

    def test_finds_russian_word(self):
        text = find_word_corpus("живу", "Русский")

        assert "Мин Ағбанда чуртапчам." in text

    def test_ignores_case_and_spaces(self):
        assert example_set(find_word_corpus(" КНИГА ", "Хакасский")) == example_set(
            find_word_corpus("книга", "Хакасский"))

    def test_language_filter_is_respected(self):
        assert find_word_corpus("живу", "Хакасский") == "Слово не найдено в корпусе"

    def test_searches_both_languages(self):
        both = find_word_corpus("книга", "Хакасский/Русский")

        assert both.count("---") > find_word_corpus("книга", "Хакасский").count("---")

    def test_limits_number_of_examples(self):
        text = find_word_corpus("книга", "Хакасский", num_examples=2)

        assert len(text.split("---")) == 2

    def test_picks_examples_at_random(self):
        # у «книга» примеров в корпусе больше, чем просят: подборки должны различаться
        texts = {find_word_corpus("книга", "Хакасский", num_examples=2) for _ in range(30)}

        assert len(texts) > 1

    def test_shows_ten_examples_by_default(self):
        # строк с «чазыда» в корпусе больше десяти — подборка должна оборваться
        text = find_word_corpus("чазыда", "Хакасский")

        assert len(text.split("---")) == 10

    def test_does_not_match_part_of_another_word(self):
        assert "Аның книгазы стол ӱстӱнде." not in find_word_corpus("книга", "Хакасский")

    def test_finds_word_at_sentence_start(self):
        assert "<b>Мин</b> Ағбанда чуртапчам." in find_word_corpus("мин", "Хакасский")

    def test_finds_word_before_punctuation(self):
        assert "Мин Ағбанда <b>чуртапчам</b>." in find_word_corpus("чуртапчам", "Хакасский")

    def test_falls_back_to_prefix_search(self):
        text = find_word_corpus("книгаз", "Хакасский")

        assert "Точных совпадений нет" in text
        assert "Аның <b>книгазы</b> стол ӱстӱнде." in text

    def test_exact_match_wins_over_prefix(self):
        assert "Точных совпадений нет" not in find_word_corpus("книга", "Хакасский")

    def test_shows_pair_once_when_word_is_on_both_sides(self):
        text = find_word_corpus("телефон", "Хакасский/Русский")

        assert text.count("Мин <b>телефон</b> алғам.") == 1

    def test_reports_unknown_word(self):
        assert find_word_corpus("абырақ", "Хакасский") == "Слово не найдено в корпусе"

    @pytest.mark.parametrize("word", ['кни"га', "AND OR", "*", "...", "123"])
    def test_survives_query_syntax_in_input(self, word):
        assert find_word_corpus(word, "Хакасский/Русский") == "Слово не найдено в корпусе"

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

    def test_falls_back_to_scan_when_random_tries_run_out(self, monkeypatch):
        monkeypatch.setattr(corpus, "MAX_RANDOM_TRIES", 0)

        assert 0 < len(get_random_kjh_example(300)) <= 300

    def test_reports_when_corpus_has_no_short_enough_sentence(self, monkeypatch):
        monkeypatch.setattr(corpus, "MAX_RANDOM_TRIES", 0)

        with pytest.raises(ValueError):
            get_random_kjh_example(1)


class TestGetRandomWordCorpus:
    def test_returns_word_language_and_its_examples(self):
        for _ in range(30):
            word, lang_in, text = get_random_word_corpus()

            assert lang_in in {"Хакасский", "Русский"}
            # слово взято из самого корпуса, поэтому пример обязан найтись точно
            assert text != "Слово не найдено в корпусе"
            assert f"<b>{word}</b>" in text.lower()
            assert "Точных совпадений нет" not in text

    def test_gives_up_instead_of_looping_forever(self, monkeypatch):
        monkeypatch.setattr(corpus, "MAX_RANDOM_TRIES", 0)

        with pytest.raises(ValueError):
            get_random_word_corpus()
