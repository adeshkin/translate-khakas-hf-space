import hashlib
import os
import random
import re
import sqlite3
import tempfile
import threading

import gradio as gr
from datasets import load_dataset

from common import DEFAULT_LANG, LANG_MAP, lang_radio, langs_for, letter_buttons

dict_hf_id = 'adeshkin/khakas-russian-parallel-corpus'
ds = load_dataset(dict_hf_id, split='train')

# Версия схемы входит в имя файла базы: при её изменении база собирается заново.
DB_SCHEMA_VERSION = 1
CREATE_TABLE_SQL = ('CREATE VIRTUAL TABLE corpus USING fts5('
                    'kjh, ru, tokenize="unicode61 remove_diacritics 0")')
# remove_diacritics 0 оставляет ӧ, ӱ отдельными буквами: «кун» и «кӱн» — разные слова.

WORD_RE = re.compile(r'[^\W\d_]+')

# Сколько раз пробуем угадать подходящую строку, прежде чем идти в перебор:
# без предела случайный выбор мог бы крутиться бесконечно.
MAX_RANDOM_TRIES = 50

# Сколько примеров показываем на одно слово.
NUM_EXAMPLES = 10


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
    # lang приходит только из LANG_MAP, не из пользовательского ввода.
    row = get_connection().execute(f'SELECT {lang} FROM corpus WHERE rowid = ?',
                                   (rowid,)).fetchone()

    return row[0]


def search_lang(lang, word, limit, prefix=False):
    query = f'{lang}:{quote_phrase(word)}' + ('*' if prefix else '')

    # ORDER BY RANDOM(): на каждый поиск подборка примеров новая. Даже у самых
    # частых слов совпадений десятки тысяч, и перебор занимает единицы миллисекунд.
    return get_connection().execute(
        'SELECT rowid, kjh, ru FROM corpus WHERE corpus MATCH ? ORDER BY RANDOM() LIMIT ?',
        (query, limit)).fetchall()


def highlight_word(text, word, prefix=False):
    """Выделяет найденное слово в примере предложения."""
    escaped = re.escape(word)
    if prefix:
        pattern = re.compile(rf'(?<![^\W\d_])({escaped}[^\W\d_]*)', re.IGNORECASE)
    else:
        pattern = re.compile(rf'(?<![^\W\d_])({escaped})(?![^\W\d_])', re.IGNORECASE)

    return pattern.sub(r'<b>\1</b>', text)


def search(langs, word, num_examples, prefix=False):
    examples = []
    seen = set()
    for lang in langs:
        # Лимит на каждый язык полный: у заимствований вроде «телефон» слово стоит
        # по обе стороны пары, и без запаса дубли съели бы места под примеры.
        for rowid, kjh_sent, ru_sent in search_lang(lang, word, num_examples, prefix):
            if rowid in seen:
                continue

            seen.add(rowid)
            if lang == 'kjh':
                kjh_sent = highlight_word(kjh_sent, word, prefix)
            else:
                ru_sent = highlight_word(ru_sent, word, prefix)
            examples.append(f'- {kjh_sent}\n\n- {ru_sent}' if lang == 'kjh'
                            else f'- {ru_sent}\n\n- {kjh_sent}')
            if len(examples) == num_examples:
                return examples

    return examples


def format_example(examples):
    if len(examples) == 0:
        return 'Слово не найдено в корпусе'

    return '\n\n---\n\n'.join(examples)


def find_word_corpus(word, lang_in, num_examples=NUM_EXAMPLES):
    word = word.strip().lower()
    if len(word) == 0:
        gr.Warning("Введите слово")
        return ""

    langs = langs_for(lang_in)

    note = ''
    examples = search(langs, word, num_examples)
    if len(examples) == 0:
        examples = search(langs, word, num_examples, prefix=True)
        if len(examples) > 0:
            note = ('*Точных совпадений нет. Показываем слова, начинающиеся '
                    f'на «{word}».*\n\n')

    return note + format_example(examples)


def get_random_kjh_example(max_text_len):
    for _ in range(MAX_RANDOM_TRIES):
        sent = get_sentence('kjh', random.randint(1, num_rows))
        if 0 < len(sent) <= max_text_len:
            return sent

    # Случайные попытки могли не угадать: добираем первым же подходящим примером.
    row = get_connection().execute(
        'SELECT kjh FROM corpus WHERE length(kjh) BETWEEN 1 AND ? LIMIT 1',
        (max_text_len,)).fetchone()
    if row is None:
        raise ValueError(f'В корпусе нет предложений короче {max_text_len} символов')

    return row[0]


def get_random_word_corpus():
    lang = random.choice(list(LANG_MAP.keys()))
    words = []
    for _ in range(MAX_RANDOM_TRIES):
        words = WORD_RE.findall(get_sentence(lang, random.randint(1, num_rows)).lower())
        if len(words) > 0:
            break
    else:
        raise ValueError('В корпусе не нашлось ни одного слова')

    word = random.choice(words)
    lang_in = LANG_MAP[lang]
    text = find_word_corpus(word, lang_in)

    return word, lang_in, text


with gr.Blocks(title="Примеры") as corpus_interface:
    gr.Markdown("Хакасско-русский корпус")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Слово",
                                    placeholder="Слово на хакасском или русском")
            letter_buttons(text_input)

            lang_input = lang_radio()

            with gr.Row():
                submit_btn = gr.Button("Найти", variant="primary")
                random_btn = gr.Button("Случайное слово")
                clear_btn = gr.Button("Очистить")

        with gr.Column():
            corpus_output = gr.Markdown(label="Примеры из корпуса",
                                        container=True,
                                        padding=True,
                                        elem_classes="result-output")

    submit_btn.click(fn=find_word_corpus,
                     inputs=[text_input, lang_input],
                     outputs=corpus_output)
    random_btn.click(fn=get_random_word_corpus,
                     inputs=None,
                     outputs=[text_input, lang_input, corpus_output])
    clear_btn.click(fn=lambda: ("", DEFAULT_LANG, ""),
                    inputs=None,
                    outputs=[text_input, lang_input, corpus_output])
