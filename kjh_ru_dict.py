import gradio as gr
from datasets import load_dataset
import random
import re

from common import DEFAULT_LANG, LANG_MAP, lang_radio, langs_for, letter_buttons

SPLIT_RE = re.compile(r'([;:])\s*(?!\s)(?=[\W\d_])')
NUM_RE = re.compile(r'(?<!<b>)(?<!<i>)(?<!<br>)(?<!\s)(?<!\d)\s*(?=1[.)])')
JOIN_RE = re.compile(r'(\d+\.(?:</[ib]>)*)<br>(?=\d+\))')
TAG_RE = re.compile(r'<([ib])>(.*?)</\1>', re.DOTALL)
EMPTY_TAG_RE = re.compile(r'<([ib])>(\s*)</\1>')
TRAIL_RE = re.compile(r'<br>(?=(?:</[ib]>)*$)')

# Границы отката словоформы к статье-основе: «ағасха» ищется как «ағас»,
# но «аалларынзар» до «аал» уже не сокращается.
MIN_STEM_LEN = 3
MAX_SUFFIX_LEN = 6

dict_hf_id = 'adeshkin/khakas-russian-dict'
ds = load_dataset(dict_hf_id, split='train')


def prepare_dict():
    word2dict_article = {'kjh': dict(),
                         'ru': dict()}
    # Колонки берутся из Arrow целиком: построчный обход датасета на порядок дороже.
    for kjh_word, ru_word, article in zip(ds['word'], ds['semgloss'], ds['field1']):
        word2dict_article['kjh'].setdefault(kjh_word.strip().lower(), []).append(article)
        word2dict_article['ru'].setdefault(ru_word.strip().lower(), []).append(article)

    return word2dict_article


word2article = prepare_dict()


def split_tag(match):
    tag, inner = match.group(1), match.group(2)
    inner = inner.replace(';', f'</{tag}> ; <{tag}>')

    return f'<{tag}>{inner}</{tag}>'


def prepare_article(article):
    article = article.replace('<і>', '<i>').replace('</і>', '</i>')
    article = TAG_RE.sub(split_tag, article)
    article = EMPTY_TAG_RE.sub(r'\2', article)
    article = SPLIT_RE.sub(r'\1<br>', article)
    article = NUM_RE.sub('<br>', article)
    article = JOIN_RE.sub(r'\1 ', article)

    return TRAIL_RE.sub('', article.strip())


def format_article(articles):
    if len(articles) == 0:
        return 'Нет слова'

    return '\n\n---\n\n'.join(prepare_article(article) for article in articles)


def lookup_word(word, lang):
    """Ищет точное совпадение, иначе самую длинную статью-основу для словоформы."""
    articles = word2article[lang]
    if word in articles:
        return word, articles[word]

    min_stem_len = max(MIN_STEM_LEN, len(word) - MAX_SUFFIX_LEN)
    for stem_len in range(len(word) - 1, min_stem_len - 1, -1):
        stem = word[:stem_len]
        if stem in articles:
            return stem, articles[stem]

    return None, []


def find_word_dict(word, lang_in):
    word = word.strip().lower()
    if len(word) == 0:
        gr.Warning("Введите слово")
        return ""

    langs = langs_for(lang_in)

    articles = []
    stems = []
    for lang in langs:
        stem, lang_articles = lookup_word(word, lang)
        articles.extend(lang_articles)
        if stem is not None and stem != word:
            stems.append(stem)

    text = format_article(articles)
    if len(stems) > 0:
        found = ', '.join(f'«{stem}»' for stem in dict.fromkeys(stems))
        text = f'*Точного совпадения нет — статьи для {found}.*\n\n{text}'

    return text


def get_random_word_dict():
    lang = random.choice(list(LANG_MAP.keys()))
    word = random.choice(list(word2article[lang].keys()))
    lang_in = LANG_MAP[lang]
    text = find_word_dict(word, lang_in)

    return word, lang_in, text


with gr.Blocks(title="Словарь") as dict_interface:
    gr.Markdown("Словарь")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Слово",
                                    placeholder="Введите слово")
            letter_buttons(text_input)

            lang_input = lang_radio()

            with gr.Row():
                submit_btn = gr.Button("Найти", variant="primary")
                random_btn = gr.Button("Случайное слово")
                clear_btn = gr.Button("Очистить")

        with gr.Column():
            dict_output = gr.Markdown(label="Результат",
                                      container=True,
                                      padding=True,
                                      elem_classes="result-output")

    submit_btn.click(fn=find_word_dict,
                     inputs=[text_input, lang_input],
                     outputs=dict_output)
    random_btn.click(fn=get_random_word_dict,
                     inputs=None,
                     outputs=[text_input, lang_input, dict_output])
    clear_btn.click(fn=lambda: ("", DEFAULT_LANG, ""),
                    inputs=None,
                    outputs=[text_input, lang_input, dict_output])
