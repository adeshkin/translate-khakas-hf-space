import pytest

import kjh_ru_dict
from kjh_ru_dict import (
    find_word_dict,
    format_article,
    get_random_word_dict,
    insert_letter,
    prepare_article,
    prepare_dict,
)


class TestPrepareDict:
    def test_indexes_words_by_both_languages(self):
        word2article = prepare_dict()

        assert set(word2article) == {"kjh", "ru"}
        assert set(word2article["kjh"]) == {"ағас", "книга"}
        assert set(word2article["ru"]) == {"дерево", "древесина", "книга"}

    def test_merges_articles_of_same_word_ignoring_case(self):
        word2article = prepare_dict()

        assert len(word2article["kjh"]["ағас"]) == 2


class TestPrepareArticle:
    def test_keeps_plain_article_as_is(self):
        assert prepare_article("<b>ағас</b> <i>сущ.</i> дерево; лес") == (
            "<b>ағас</b> <i>сущ.</i> дерево; лес"
        )

    def test_replaces_cyrillic_i_in_tags(self):
        assert prepare_article("<і>сущ.</і> дерево") == "<i>сущ.</i> дерево"

    def test_splits_enumeration_inside_tag(self):
        assert prepare_article("<i>дерево; лес; тайга</i>") == (
            "<i>дерево</i> ;<br><i> лес</i> ;<br><i> тайга</i>"
        )

    def test_breaks_line_before_first_numbered_meaning(self):
        assert prepare_article("<b>пар</b> 1) идти 2) ехать") == (
            "<b>пар</b><br>1) идти 2) ехать"
        )

    def test_keeps_numbered_group_on_one_line(self):
        assert prepare_article("<b>пар</b> <i>гл.</i> 1. 1) идти 2) ехать") == (
            "<b>пар</b> <i>гл.</i><br>1. 1) идти 2) ехать"
        )

    def test_drops_empty_tags(self):
        assert "<i></i>" not in prepare_article("<b>сӧс</b> <i></i> слово")

    def test_drops_trailing_break(self):
        assert not prepare_article("слово; <br>").endswith("<br><br>")


class TestFormatArticle:
    def test_reports_missing_word(self):
        assert format_article([]) == "Нет слова"

    def test_joins_articles_with_separator(self):
        text = format_article(["<b>а</b> раз", "<b>а</b> два"])

        assert text == "<b>а</b> раз\n\n---\n\n<b>а</b> два"


class TestFindWordDict:
    def test_finds_khakas_word(self):
        text = find_word_dict("ағас", "Хакасский")

        assert "дерево" in text
        assert "древесина" in text

    def test_finds_russian_word(self):
        assert "дерево" in find_word_dict("дерево", "Русский")

    def test_ignores_case_and_spaces(self):
        assert find_word_dict("  АҒАС ", "Хакасский") == find_word_dict("ағас", "Хакасский")

    def test_searches_both_languages(self):
        text = find_word_dict("книга", "Хакасский/Русский")

        assert text.count("---") == 1

    def test_language_filter_is_respected(self):
        assert find_word_dict("дерево", "Хакасский") == "Нет слова"

    def test_reports_unknown_word(self):
        assert find_word_dict("абырақ", "Хакасский") == "Нет слова"

    def test_warns_on_empty_input(self):
        with pytest.warns(UserWarning, match="Введите слово"):
            assert find_word_dict("   ", "Хакасский") == ""


class TestGetRandomWordDict:
    def test_returns_word_language_and_its_article(self):
        for _ in range(20):
            word, lang_in, text = get_random_word_dict()

            assert lang_in in {"Хакасский", "Русский"}
            assert word in kjh_ru_dict.word2article["kjh" if lang_in == "Хакасский" else "ru"]
            assert text == find_word_dict(word, lang_in)
            assert text != "Нет слова"


class TestInsertLetter:
    def test_appends_letter(self):
        assert insert_letter("ӧ")("сӧ") == "сӧӧ"

    def test_handles_empty_textbox(self):
        assert insert_letter("і")(None) == "і"
        assert insert_letter("і")("") == "і"
