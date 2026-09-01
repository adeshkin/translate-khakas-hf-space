import hashlib
import os
import random
import re
import sqlite3
import tempfile
import threading

import gradio as gr
from datasets import load_dataset

dict_hf_id = 'adeshkin/khakas-russian-parallel-corpus'
ds = load_dataset(dict_hf_id, split='train')

# Версия схемы входит в имя файла базы: при её изменении база собирается заново.
DB_SCHEMA_VERSION = 1
CREATE_TABLE_SQL = ('CREATE VIRTUAL TABLE corpus USING fts5('
                    'kjh, ru, tokenize="unicode61 remove_diacritics 0")')
# remove_diacritics 0 оставляет ӧ, ӱ отдельными буквами: «кун» и «кӱн» — разные слова.

WORD_RE = re.compile(r'[^\W\d_]+')

lang_map = {'kjh': 'Хакасский',
            'ru': 'Русский'}


def dataset_fingerprint():
    parts = (getattr(ds, '_fingerprint', ''), repr(getattr(ds, 'cache_files', '')), len(ds))

    return hashlib.sha1(repr(parts).encode()).hexdigest()[:16]


def build_index():
    """Собирает полнотекстовый индекс корпуса во временном файле.

    Готовый файл переиспользуется, поэтому повторный запуск стартует мгновенно.
    """
    db_path = os.path.join(tempfile.gettempdir(),
                           f'kjh_corpus_v{DB_SCHEMA_VERSION}_{dataset_fingerprint()}.db')
    if os.path.exists(db_path):
        return db_path

    tmp_path = f'{db_path}.{os.getpid()}.tmp'
    try:
        con = sqlite3.connect(tmp_path)
        try:
            con.execute('PRAGMA journal_mode = OFF')
            con.execute('PRAGMA synchronous = OFF')
            con.execute(CREATE_TABLE_SQL)
            # Колонки берутся из Arrow целиком: построчный обход датасета на порядок дороже.
            con.executemany('INSERT INTO corpus(kjh, ru) VALUES (?, ?)',
                            zip(ds['kjh'], ds['ru']))
            con.commit()
        finally:
            con.close()
        # Подмена файла целиком: параллельная сборка не отдаст недособранную базу.
        os.replace(tmp_path, db_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    return db_path


db_path = build_index()
num_rows = len(ds)
connections = threading.local()


def get_connection():
    """Отдаёт соединение текущего потока: gradio обрабатывает запросы в пуле потоков."""
    con = getattr(connections, 'con', None)
    if con is None:
        con = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        connections.con = con

    return con


def quote_phrase(word):
    """Превращает любой ввод в одну фразу FTS5, чтобы синтаксис MATCH не ломался."""
    return '"' + word.replace('"', '""') + '"'


def get_sentence(lang, rowid):
    # lang приходит только из lang_map, не из пользовательского ввода.
    row = get_connection().execute(f'SELECT {lang} FROM corpus WHERE rowid = ?',
                                   (rowid,)).fetchone()

    return row[0]


def search_lang(lang, word, limit, prefix=False):
    query = f'{lang}:{quote_phrase(word)}' + ('*' if prefix else '')
    rows = get_connection().execute('SELECT kjh, ru FROM corpus WHERE corpus MATCH ? LIMIT ?',
                                    (query, limit)).fetchall()

    return [f'{kjh_sent}\n\n{ru_sent}' if lang == 'kjh' else f'{ru_sent}\n\n{kjh_sent}'
            for kjh_sent, ru_sent in rows]


def search(langs, word, num_examples, prefix=False):
    examples = []
    for lang in langs:
        examples.extend(search_lang(lang, word, num_examples - len(examples), prefix))
        if len(examples) == num_examples:
            break

    return examples


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

    if lang_in == 'Хакасский/Русский':
        langs = ['kjh', 'ru']
    else:
        langs = ['ru'] if lang_in == 'Русский' else ['kjh']

    note = ''
    examples = search(langs, word, num_examples)
    if len(examples) == 0:
        examples = search(langs, word, num_examples, prefix=True)
        if len(examples) > 0:
            note = f'*Точных совпадений нет — слова, начинающиеся на «{word}».*\n\n'

    return note + format_example(examples)


def get_random_kjh_example(max_text_len):
    sent = ''
    while len(sent) == 0 or len(sent) > max_text_len:
        sent = get_sentence('kjh', random.randint(1, num_rows))

    return sent


def get_random_word_corpus():
    lang = random.choice(list(lang_map.keys()))
    words = []
    while len(words) == 0:
        words = WORD_RE.findall(get_sentence(lang, random.randint(1, num_rows)).lower())

    word = random.choice(words)
    lang_in = lang_map[lang]
    text = find_word_corpus(word, lang_in)

    return word, lang_in, text


def insert_letter(letter):
    def _insert(text):
        return (text or "") + letter

    return _insert


with gr.Blocks(title="Корпус") as corpus_interface:
    gr.Markdown("## Корпус")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Слово",
                                    placeholder="Введите слово")
            with gr.Row(elem_classes="khakas-letters"):
                for letter in "іғңҷӧӱ":
                    letter_btn = gr.Button(letter, size="sm", scale=0)
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
            corpus_output = gr.Markdown(label="Результат",
                                        container=True,
                                        padding=True)

    submit_btn.click(fn=find_word_corpus,
                     inputs=[text_input, lang_input],
                     outputs=corpus_output)
    random_btn.click(fn=get_random_word_corpus,
                     inputs=None,
                     outputs=[text_input, lang_input, corpus_output])
    clear_btn.click(fn=lambda: ("", "Хакасский", ""),
                    inputs=None,
                    outputs=[text_input, lang_input, corpus_output])
