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

.tk-about {{
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}}

.tk-about-lead {{
    margin: 0;
    font-size: 1rem;
    line-height: 1.45;
    color: var(--body-text-color);
}}

.tk-about-list {{
    margin: 0;
    padding-left: 1.1rem;
    list-style: disc;
    font-size: 0.95rem;
    line-height: 1.5;
    color: var(--body-text-color-subdued);
}}

.tk-about-list b {{
    font-weight: 600;
    color: var(--body-text-color);
}}

.tk-links {{
    display: flex;
    flex-direction: column;
    gap: 1.4rem;
    padding: 0.25rem 0 0.5rem;
}}

.tk-links-group-title {{
    margin: 0 0 0.6rem;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--body-text-color-subdued);
}}

.tk-links-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
    gap: 0.6rem;
}}

.tk-link-card {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 0.9rem;
    border: 1px solid var(--border-color-primary);
    border-radius: var(--radius-lg);
    background: var(--background-fill-primary);
    color: var(--body-text-color) !important;
    text-align: left;
    text-decoration: none !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}}

.tk-link-card:hover {{
    border-color: #0077ff;
    box-shadow: 0 2px 10px rgba(0, 119, 255, 0.15);
    transform: translateY(-1px);
}}

.tk-link-icon {{
    flex-shrink: 0;
    width: 2.1rem;
    font-size: 1.5rem;
    line-height: 1.2;
    text-align: center;
}}

.tk-link-icon svg {{
    width: 1.4rem;
    height: 1.4rem;
    vertical-align: -0.2em;
}}

.tk-link-icon_tg svg {{
    fill: #29a1d4;
}}

.tk-link-icon_vk svg {{
    fill: #0077ff;
}}

.tk-link-icon_gh svg {{
    fill: var(--body-text-color);
}}

.tk-link-text {{
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    min-width: 0;
}}

.tk-link-title {{
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.3;
}}

.tk-link-desc {{
    font-size: 0.85rem;
    line-height: 1.3;
    color: var(--body-text-color-subdued);
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

VK_URL = "https://vk.ru/translate_khakas"
TG_URL = "https://t.me/translate_khakas"
GITHUB_URL = "https://github.com/adeshkin/translate-khakas-hf-space"
CORPUS_URL = "https://huggingface.co/datasets/adeshkin/khakas-russian-parallel-corpus"
DICT_URL = "https://huggingface.co/datasets/adeshkin/khakas-russian-dict"
KEYBOARD_MOBILE_URL = "https://yandex.ru/yandexapp/ru/keyboard/"
KEYBOARD_DESKTOP_URL = "https://dict.khakbooks.ru/keyboard"
TRANSLATOR_URL = "https://translate.yandex.ru/?source_lang=kjh&target_lang=ru"
MODELS_URL = "https://huggingface.co/collections/adeshkin/khakas-translation"
MT_CODE_URL = "https://github.com/adeshkin/khakas-mt"

VK_ICON = '<svg xmlns="http://www.w3.org/2000/svg" fill="#0077ff" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M1.406 1.406C0 2.812 0 5.075 0 9.6v.8c0 4.525 0 6.788 1.406 8.194S5.075 20 9.6 20h.8c4.525 0 6.788 0 8.194-1.406S20 14.925 20 10.4v-.8c0-4.525 0-6.788-1.406-8.194S14.925 0 10.4 0h-.8C5.075 0 2.812 0 1.406 1.406m1.969 4.678c.108 5.2 2.708 8.325 7.266 8.325h.259v-2.976c1.675.167 2.941 1.392 3.45 2.976h2.366c-.65-2.367-2.358-3.675-3.425-4.175 1.067-.617 2.567-2.117 2.925-4.15h-2.15c-.466 1.65-1.85 3.15-3.166 3.291V6.084H8.75v5.766c-1.334-.333-3.017-1.95-3.092-5.766z" clip-rule="evenodd"></path></svg>'
TG_ICON = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0m5.03 7.229c-.18 1.898-.962 6.502-1.36 8.627-.168.9-.5 1.201-.82 1.23-.697.065-1.226-.46-1.901-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212-.07-.062-.174-.041-.249-.024-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635.1-.002.322.023.466.14a.506.506 0 0 1 .17.325c.016.093.036.306.02.472"></path></svg>'
GITHUB_ICON = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8"></path></svg>'

ABOUT_HTML = (
    '<div class="tk-about">'
    '<p class="tk-about-lead">TranslateKhak — набор онлайн-инструментов для работы '
    'с хакасским языком.</p>'
    '<ul class="tk-about-list">'
    '<li><b>Словарь</b> — перевод слова по хакасско-русскому словарю</li>'
    '<li><b>Корпус</b> — примеры употребления слова в параллельном корпусе</li>'
    '<li><b>Озвучка</b> — синтез речи на хакасском языке</li>'
    '</ul>'
    '<p class="tk-about-lead">Материалы и ресурсы по хакасскому языку:</p>'
    '</div>'
)


LINK_GROUPS = [
    ("Данные", [
        ("📚", "", "Хакасско-русский параллельный корпус", "Датасет предложений на Hugging Face", CORPUS_URL),
        ("📖", "", "Хакасско-русский словарь", "Датасет словарных статей на Hugging Face", DICT_URL),
    ]),
    ("Модели перевода", [
        ("🤖", "", "Модели и датасеты", "Коллекция Khakas Translation на Hugging Face", MODELS_URL),
        (GITHUB_ICON, "tk-link-icon_gh", "Код обучения моделей", "Дообучение NLLB-200 и Hy-MT2 на GitHub", MT_CODE_URL),
    ]),
    ("Хакасская клавиатура", [
        ("📱", "", "Клавиатура на телефон", "Яндекс Клавиатура с поддержкой хакасского языка", KEYBOARD_MOBILE_URL),
        ("💻", "", "Драйверы на компьютер", "Раскладка хакасской клавиатуры для ПК", KEYBOARD_DESKTOP_URL),
    ]),
    ("Сервисы", [
        ("🌐", "", "Яндекс Переводчик", "Перевод с хакасского и на хакасский язык", TRANSLATOR_URL),
    ]),
    ("Проект", [
        (TG_ICON, "tk-link-icon_tg", "Канал в Telegram", "Новости и обновления проекта", TG_URL),
        (VK_ICON, "tk-link-icon_vk", "Сообщество ВКонтакте", "Новости и обновления проекта", VK_URL),
        (GITHUB_ICON, "tk-link-icon_gh", "Репозиторий GitHub", "Исходный код проекта", GITHUB_URL),
    ]),
]


def render_link_card(icon, icon_class, title, desc, url):
    return (
        f'<a class="tk-link-card" href="{url}" target="_blank" rel="noopener noreferrer">'
        f'<span class="tk-link-icon {icon_class}">{icon}</span>'
        f'<span class="tk-link-text">'
        f'<span class="tk-link-title">{title}</span>'
        f'<span class="tk-link-desc">{desc}</span>'
        f'</span></a>'
    )


def render_links_html():
    groups = []
    for group_title, links in LINK_GROUPS:
        cards = "".join(render_link_card(*link) for link in links)
        groups.append(
            f'<div class="tk-links-group">'
            f'<div class="tk-links-group-title">{group_title}</div>'
            f'<div class="tk-links-grid">{cards}</div>'
            f'</div>'
        )
    return f'<div class="tk-links">{ABOUT_HTML}{"".join(groups)}</div>'


LINKS_HTML = render_links_html()

FOOTER_HTML = f"""
<div class="tk-footer">
  <a href="{VK_URL}" class="social-link social-link_vk" title="Сообщество ВКонтакте" target="_blank" rel="noopener noreferrer">{VK_ICON}ВКонтакте</a>
</div>
"""

with gr.Blocks() as links_page:
    gr.HTML(LINKS_HTML)

demo = gr.TabbedInterface([dict_interface, corpus_interface, tts_interface, links_page],
                          [dict_interface.title, corpus_interface.title, tts_interface.title, "Ссылки"],
                          title='TranslateKhak')

with demo:
    gr.HTML(FOOTER_HTML)

demo.launch(css=CUSTOM_CSS)
