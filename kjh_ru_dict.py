import gradio as gr
from datasets import load_dataset
import random

dict_hf_id = 'adeshkin/khakas-russian-dict'
ds = load_dataset(dict_hf_id, split='train')


def prepare_dict():
    word2dict_article = {'kjh': dict(),
                         'ru': dict()}
    for row in ds:
        kjh_word = row['word'].strip().lower()
        ru_word = row['semgloss'].strip().lower()
        if kjh_word not in word2dict_article['kjh']:
            word2dict_article['kjh'][kjh_word] = []
        word2dict_article['kjh'][kjh_word].append(row['field1'])

        if ru_word not in word2dict_article['ru']:
            word2dict_article['ru'][ru_word] = []
        word2dict_article['ru'][ru_word].append(row['field1'])

    return word2dict_article


word2article = prepare_dict()

lang_map = {'kjh': 'Хакасский',
            'ru': 'Русский'}


def format_article(articles):
    if len(articles) == 0:
        return 'Нет слова'

    text = '\n\n---\n\n'.join(articles).replace('<і>', '<i>').replace('</і>', '</i>')

    return text


def find_word_dict(word, lang_in):
    word = word.strip().lower()
    if len(word) == 0:
        gr.Warning("Введите слово")
        return ""

    if lang_in == 'Хакасский/Русский':
        articles = []
        for lang in ['kjh', 'ru']:
            if word in word2article[lang]:
                articles.extend(word2article[lang][word])
    else:
        lang = 'ru' if lang_in == 'Русский' else 'kjh'
        articles = []
        if word in word2article[lang]:
            articles.extend(word2article[lang][word])

    text = format_article(articles)

    return text


def get_random_word_dict():
    lang = random.choice(list(lang_map.keys()))
    word = random.choice(list(word2article[lang].keys()))
    lang_in = lang_map[lang]
    text = find_word_dict(word, lang_in)

    return word, lang_in, text


def insert_letter(letter):
    def _insert(text):
        return (text or "") + letter

    return _insert


with gr.Blocks(title="Словарь") as dict_interface:
    gr.Markdown("Словарь")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Слово",
                                    placeholder="Введите слово")
            with gr.Row(elem_classes="khakas-letters"):
                for letter in "іғңҷӧӱ":
                    letter_btn = gr.Button(letter, size="sm")
                    letter_btn.click(insert_letter(letter), inputs=text_input, outputs=text_input)

            lang_input = gr.Radio(
                choices=["Хакасский", "Русский", "Хакасский/Русский"],
                value="Хакасский",
                label="Язык"
            )

            with gr.Row():
                submit_btn = gr.Button("Найти", variant="primary")
                random_btn = gr.Button("Случайное слово")
                clear_btn = gr.Button("Очистить")

        with gr.Column():
            dict_output = gr.Markdown(label="Результат",
                                      container=True,
                                      padding=True)

    submit_btn.click(fn=find_word_dict,
                     inputs=[text_input, lang_input],
                     outputs=dict_output)
    random_btn.click(fn=get_random_word_dict,
                     inputs=None,
                     outputs=[text_input, lang_input, dict_output])
    clear_btn.click(fn=lambda: ("", "Хакасский", ""),
                    inputs=None,
                    outputs=[text_input, lang_input, dict_output])
