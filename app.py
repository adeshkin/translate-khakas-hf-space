import gradio as gr
import os
import urllib.parse

from kjh_ru_dict import dict_interface
from corpus import corpus_interface
from tts import tts_interface

image_dir = os.path.join(os.path.dirname(__file__), "images")

def load_svg_encoded(filename):
    path = os.path.join(image_dir, filename)
    with open(path, encoding="utf-8") as f:
        return urllib.parse.quote(f.read())


_BACK_SVG_ENCODED = load_svg_encoded("back.svg")
_LOGO_SVG_ENCODED = load_svg_encoded("logo.svg")

CUSTOM_CSS = f"""
.gradio-container {{
    background-image: url('data:image/svg+xml,{_BACK_SVG_ENCODED}');
    background-repeat: no-repeat;
    background-position: max(0px, 50%) bottom;
    background-size: auto 65vh;
    background-attachment: fixed;
}}
"""

demo = gr.TabbedInterface([dict_interface, corpus_interface, tts_interface],
                          [dict_interface.title, corpus_interface.title, tts_interface.title],
                          title='TranslateKhak')
demo.launch(css=CUSTOM_CSS)
