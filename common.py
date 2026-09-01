"""Общие для вкладок константы и элементы интерфейса."""

import gradio as gr

LANG_MAP = {'kjh': 'Хакасский',
            'ru': 'Русский'}

DEFAULT_LANG = 'Хакасский'
LANG_CHOICES = ['Хакасский', 'Русский', 'Хакасский/Русский']

KHAKAS_LETTERS = 'іғңҷӧӱ'


def langs_for(lang_in):
    """Переводит выбор пользователя в коды колонок датасета."""
    if lang_in == 'Хакасский/Русский':
        return ['kjh', 'ru']

    return ['ru'] if lang_in == 'Русский' else ['kjh']


def insert_letter(letter):
    def _insert(text):
        return (text or "") + letter

    return _insert


def letter_buttons(text_input):
    """Ряд кнопок с хакасскими буквами: дописывают букву в поле ввода."""
    with gr.Row(elem_classes="khakas-letters"):
        for letter in KHAKAS_LETTERS:
            letter_btn = gr.Button(letter, size="sm", scale=0)
            letter_btn.click(insert_letter(letter), inputs=text_input, outputs=text_input)


def lang_radio():
    return gr.Radio(choices=LANG_CHOICES,
                    value=DEFAULT_LANG,
                    label="Язык")
