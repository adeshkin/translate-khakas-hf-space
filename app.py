import gradio as gr
import os
import urllib.parse

from kjh_ru_dict import dict_interface
from corpus import corpus_interface
from tts import tts_interface
from about import links_interface, VK_URL

image_dir = os.path.join(os.path.dirname(__file__), "images")


def load_svg_encoded(filename):
    path = os.path.join(image_dir, filename)
    with open(path, encoding="utf-8") as f:
        return urllib.parse.quote(f.read())


_BACK_SVG_ENCODED = load_svg_encoded("back.svg")
_LOGO_SVG_ENCODED = load_svg_encoded("logo.svg")

CUSTOM_CSS = f"""
.gradio-container {{
    --input-text-size: 18px;

    background-image: url('data:image/svg+xml,{_BACK_SVG_ENCODED}');
    background-repeat: no-repeat;
    background-position: max(0px, 50%) bottom;
    background-size: auto 50vh;
    background-attachment: fixed;
}}

.gradio-container h1 {{
    font-size: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
}}

.gradio-container h1::before {{
    content: '';
    flex-shrink: 0;
    width: 1.2em;
    height: 1.2em;
    background-image: url('data:image/svg+xml,{_LOGO_SVG_ENCODED}');
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain;
}}

.gradio-container .tab-wrapper button {{
    font-size: 20px;
}}

.gradio-container .prose:not(:has(h1)) {{
    font-size: 19px;
}}

.dict-output p {{
    margin: 0;
}}

.dict-output hr {{
    margin: 0.6rem 0;
}}

.khakas-letters {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.15rem;
    margin: -0.5rem 0 0.75rem;
}}

.khakas-letters > * {{
    flex: 0 0 auto !important;
    width: auto !important;
    margin: 0 !important;
    padding: 0 !important;
}}

.khakas-letters button {{
    width: 2.8em !important;
    min-width: 2.8em !important;
    max-width: 2.8em !important;
    height: 2.2em !important;
    padding: 0 !important;
    flex-grow: 0 !important;
    flex-shrink: 0 !important;
    font-size: 17px;
}}


.tk-footer {{
    display: flex;
    justify-content: center;
    padding: 0.5rem 0 1rem;
}}

.social-link {{
    display: inline-flex;
    align-items: flex-start;
    gap: 0.15rem;
    color: var(--body-text-color-subdued) !important;
    text-decoration: none !important;
    text-align: left;
    font-size: 1.15rem;
}}

.social-link:hover {{
    color: #0077ff !important;
}}

.social-link svg {{
    width: 1.25em;
    height: 1.25em;
    flex-shrink: 0;
    color: #0077ff;
    fill: #0077ff !important;
}}
"""

VK_ICON = '<svg xmlns="http://www.w3.org/2000/svg" fill="#0077ff" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M1.406 1.406C0 2.812 0 5.075 0 9.6v.8c0 4.525 0 6.788 1.406 8.194S5.075 20 9.6 20h.8c4.525 0 6.788 0 8.194-1.406S20 14.925 20 10.4v-.8c0-4.525 0-6.788-1.406-8.194S14.925 0 10.4 0h-.8C5.075 0 2.812 0 1.406 1.406m1.969 4.678c.108 5.2 2.708 8.325 7.266 8.325h.259v-2.976c1.675.167 2.941 1.392 3.45 2.976h2.366c-.65-2.367-2.358-3.675-3.425-4.175 1.067-.617 2.567-2.117 2.925-4.15h-2.15c-.466 1.65-1.85 3.15-3.166 3.291V6.084H8.75v5.766c-1.334-.333-3.017-1.95-3.092-5.766z" clip-rule="evenodd"></path></svg>'

FOOTER_HTML = f"""
<div class="tk-footer">
  <a href="{VK_URL}" class="social-link" title="Сообщество ВКонтакте" target="_blank" rel="noopener noreferrer">{VK_ICON}ВКонтакте</a>
</div>
"""

demo = gr.TabbedInterface([dict_interface, corpus_interface, tts_interface, links_interface],
                          [dict_interface.title, corpus_interface.title, tts_interface.title, links_interface.title],
                          title='TranslateKhak')

with demo:
    gr.HTML(FOOTER_HTML)

demo.launch(css=CUSTOM_CSS)
