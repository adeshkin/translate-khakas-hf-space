import gradio as gr
import pytest

from common import (
    DEFAULT_LANG,
    KHAKAS_LETTERS,
    insert_letter,
    lang_radio,
    langs_for,
    letter_buttons,
)


class TestInsertLetter:
    def test_appends_letter(self):
        assert insert_letter("ӧ")("сӧ") == "сӧӧ"

    def test_handles_empty_textbox(self):
        assert insert_letter("і")(None) == "і"
        assert insert_letter("і")("") == "і"


class TestLangsFor:
    @pytest.mark.parametrize("lang_in, expected", [
        ("Хакасский", ["kjh"]),
        ("Русский", ["ru"]),
        ("Хакасский/Русский", ["kjh", "ru"]),
    ])
    def test_maps_choice_to_dataset_columns(self, lang_in, expected):
        assert langs_for(lang_in) == expected


class TestLetterButtons:
    def test_adds_a_button_per_khakas_letter(self):
        with gr.Blocks() as demo:
            text_input = gr.Textbox()
            letter_buttons(text_input)

        labels = [block.value for block in demo.blocks.values()
                  if isinstance(block, gr.Button)]

        assert labels == list(KHAKAS_LETTERS)


class TestLangRadio:
    def test_every_choice_is_understood_by_langs_for(self):
        with gr.Blocks():
            radio = lang_radio()

        for _, choice in radio.choices:
            assert langs_for(choice)

    def test_starts_on_default_language(self):
        with gr.Blocks():
            assert lang_radio().value == DEFAULT_LANG
