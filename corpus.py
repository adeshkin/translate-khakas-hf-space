from datasets import load_dataset
import random
import gradio as gr
from razdel import tokenize

dict_hf_id = 'adeshkin/khakas-russian-parallel-corpus'
ds = load_dataset(dict_hf_id, split='train')


def prepare_corpus():
    lang2corpus_words = {'kjh': set(), 'ru': set()}
    for row in ds:
        kjh_sent = row['kjh'].lower()
        ru_sent = row['ru'].lower()
        kjh_words = [token.text for token in tokenize(kjh_sent) if token.text.isalpha()]
        ru_words = [token.text for token in tokenize(ru_sent) if token.text.isalpha()]
        lang2corpus_words['kjh'].update(set(kjh_words))
        lang2corpus_words['ru'].update(set(ru_words))

    return lang2corpus_words


lang2words = prepare_corpus()
lang_map = {'kjh': 'Хакасский',
            'ru': 'Русский'}


def format_example(article):
    if len(article) == 0:
        return 'Нет слова в корпусе'

    text = '\n\n---\n\n'.join(article)

    return text


def find_word_corpus(word, lang_in, num_examples=5):
    word = word.strip().lower()
    if len(word) == 0:
        gr.Warning("Введите слово")
        return ""

    word = ' ' + word + ' '
    examples = []
    for row in ds:
        if lang_in == 'Хакасский/Русский':
            for lang in ['kjh', 'ru']:
                text = row[lang].lower()
                if word in text:
                    lang1 = 'kjh' if lang == 'ru' else 'ru'
                    example = f'{row[lang]}\n\n{row[lang1]}'
                    examples.append(example)
        else:
            lang = 'ru' if lang_in == 'Русский' else 'kjh'
            text = row[lang].lower()
            if word in text:
                lang1 = 'kjh' if lang == 'ru' else 'ru'
                example = f'{row[lang]}\n\n{row[lang1]}'
                examples.append(example)

        if len(examples) == num_examples:
            break

    text = format_example(examples)

    return text


def get_random_kjh_example(max_text_len):
    sent = ''
    while len(sent) == 0 or len(sent) > max_text_len:
        row = random.choice(ds)
        sent = row['kjh']

    return sent


def get_random_word_corpus():
    lang = random.choice(list(lang_map.keys()))
    word = random.choice(list(lang2words[lang]))
    lang_in = lang_map[lang]
    text = find_word_corpus(word, lang_in)

    return word, lang_in, text


with gr.Blocks(title="Корпус") as corpus_interface:
    gr.Markdown("Корпус")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Слово",
                                    placeholder="Введите слово")

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
            corpus_output = gr.Markdown(label="Результат")

    submit_btn.click(fn=find_word_corpus,
                     inputs=[text_input, lang_input],
                     outputs=corpus_output)
    random_btn.click(fn=get_random_word_corpus,
                     inputs=None,
                     outputs=[text_input, lang_input, corpus_output])
    clear_btn.click(fn=lambda: ("", "Хакасский", ""),
                    inputs=None,
                    outputs=[text_input, lang_input, corpus_output])
