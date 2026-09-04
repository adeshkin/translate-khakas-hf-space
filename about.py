import gradio as gr

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


LINK_GROUPS = [
    ("Данные", [
        ("📚", "Хакасско-русский корпус", "Датасет параллельных предложений на Hugging Face", CORPUS_URL),
        ("📖", "Хакасско-русский словарь", "Датасет словарных статей на Hugging Face", DICT_URL),
    ]),
    ("Датасеты и модели", [
        ("🤖", "Коллекция текстов и нейросетей для хакасского языка", "Модели и датасеты Khakas Translation на Hugging Face", MODELS_URL),
        ("⚙️", "Код обучения модели машинного перевода", "Дообучение NLLB-200 и Hy-MT2 на GitHub", MT_CODE_URL),
    ]),
    ("Хакасская клавиатура", [
        ("📱", "Клавиатура на телефон", "Яндекс Клавиатура с поддержкой хакасского языка", KEYBOARD_MOBILE_URL),
        ("💻", "Клавиатура на компьютер", "Драйвер хакасской клавиатуры для ПК", KEYBOARD_DESKTOP_URL),
    ]),
    ("Сервисы", [
        ("🌐", "Яндекс Переводчик", "Перевод с хакасского и на хакасский язык", TRANSLATOR_URL),
    ]),
    ("Проект", [
        ("👥", "Сообщество ВКонтакте", "Новости и обновления проекта", VK_URL),
        ("✈️", "Телеграм-канал", "Технические новости и обновления проекта", TG_URL),
        ("🐙", "Репозиторий GitHub", "Исходный код проекта", GITHUB_URL),
    ]),
]

with gr.Blocks(title="Ссылки") as links_interface:
    for group_title, group_links in LINK_GROUPS:
        gr.Markdown(f"### {group_title}")
        with gr.Row(equal_height=True):
            for icon, link_title, link_desc, link_url in group_links:
                gr.Button(f"{icon}  {link_title}", link=link_url, variant="secondary", size="lg")
