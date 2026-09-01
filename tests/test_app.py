"""Смоук-тест сборки приложения: интерфейс должен собираться без ошибок."""

import importlib
import inspect
import sys
import urllib.parse

import gradio as gr
import pytest

import about


@pytest.fixture
def app_module(monkeypatch):
    """Импортирует app.py, не поднимая сервер (`demo.launch` заглушен)."""
    launch_calls = []
    monkeypatch.setattr(
        gr.Blocks,
        "launch",
        lambda self, **kwargs: launch_calls.append((self, kwargs)),
    )
    sys.modules.pop("app", None)
    try:
        module = importlib.import_module("app")
        module.launch_calls = launch_calls
        yield module
    finally:
        sys.modules.pop("app", None)


def test_app_builds_and_launches(app_module):
    assert len(app_module.launch_calls) == 1


def test_launch_gets_custom_css(app_module):
    _, kwargs = app_module.launch_calls[0]

    assert "khakas-letters" in kwargs["css"]


def test_launch_accepts_css_argument():
    # css передаётся в launch(), а не в конструктор Blocks — проверяем, что
    # установленная версия gradio такой аргумент поддерживает.
    assert "css" in inspect.signature(gr.Blocks.launch).parameters


def test_tabs_are_in_expected_order(app_module):
    titles = [
        app_module.dict_interface.title,
        app_module.corpus_interface.title,
        app_module.tts_interface.title,
        app_module.links_interface.title,
    ]

    assert titles == ["Словарь", "Примеры", "Озвучка", "Ссылки"]


def test_footer_links_to_vk(app_module):
    assert about.VK_URL in app_module.FOOTER_HTML


def test_svg_images_are_embedded(app_module):
    for filename in ("back.svg", "logo.svg"):
        encoded = app_module.load_svg_encoded(filename)

        assert urllib.parse.unquote(encoded).lstrip().startswith("<")
        assert encoded in app_module.CUSTOM_CSS


def test_all_links_are_absolute_urls():
    urls = [url for _, links in about.LINK_GROUPS for *_, url in links]

    assert urls
    for url in urls:
        assert url.startswith("https://"), url
