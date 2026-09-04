---
title: TranslateKhak
emoji: 📚
colorFrom: green
colorTo: green
sdk: gradio
sdk_version: 6.26.0
python_version: '3.12'
app_file: app.py
pinned: false
short_description: khakas dict | corpus | tts
---

<div align="center">

# 📚 TranslateKhak

**Khakas–Russian dictionary, parallel corpus and text-to-speech — in one Gradio app.**

### 👉 [**Try it live — adeshkin-translate-khakas.hf.space**](https://adeshkin-translate-khakas.hf.space/) 👈

[![Space](https://img.shields.io/badge/🤗%20Hugging%20Face-Space-green)](https://adeshkin-translate-khakas.hf.space/)
[![Gradio](https://img.shields.io/badge/Gradio-6.26.0-orange)](https://gradio.app)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![VK](https://img.shields.io/badge/VK-Community-0077ff)](https://vk.ru/translate_khakas)
[![Telegram](https://img.shields.io/badge/Telegram-Channel-2AABEE)](https://t.me/translate_khakas)

</div>

---

This README is a **build-it-yourself guide**: it walks through how the app is put together
so you can create the same thing for your own low-resource language.

## Table of contents

- [What the app does](#what-the-app-does)
- [Architecture](#architecture)
- [Step 1 — Create the Space](#step-1--create-the-space)
- [Step 2 — Prepare the datasets](#step-2--prepare-the-datasets)
- [Step 3 — Dictionary tab](#step-3--dictionary-tab)
- [Step 4 — Corpus tab (FTS5 full-text search)](#step-4--corpus-tab-fts5-full-text-search)
- [Step 5 — TTS tab](#step-5--tts-tab)
- [Step 6 — Links tab](#step-6--links-tab)
- [Step 7 — Assemble app.py](#step-7--assemble-apppy)
- [⚠️ ZeroGPU: the required `@spaces.GPU` stub](#️-zerogpu-the-required-spacesgpu-stub)
- [Step 8 — Tests without network or models](#step-8--tests-without-network-or-models)
- [Step 9 — CI: GitHub → Hugging Face sync](#step-9--ci-github--hugging-face-sync)
- [Run locally](#run-locally)
- [Performance notes](#performance-notes)
- [Project links](#project-links)

---

## What the app does

| Tab | Module | What it does |
|---|---|---|
| 📖 **Словарь** (Dictionary) | [`kjh_ru_dict.py`](kjh_ru_dict.py) | Looks up a Khakas or Russian word in ~20k dictionary entries. Falls back to stemming when the exact word form is missing. |
| 📚 **Примеры** (Examples) | [`corpus.py`](corpus.py) | Finds real sentence pairs containing the word, using an SQLite FTS5 index over the parallel corpus. |
| 🔊 **Озвучка** (TTS) | [`tts.py`](tts.py) | Synthesises Khakas speech with a fine-tuned Silero model, two voices. |
| 🔗 **Ссылки** (Links) | [`about.py`](about.py) | Buttons to datasets, models, keyboards and community channels. |

Shared UI pieces (language radio, Khakas letter buttons `і ғ ң ҷ ӧ ӱ`) live in [`common.py`](common.py).

## Architecture

```
app.py                 # TabbedInterface + custom CSS + footer + launch()
├── kjh_ru_dict.py     # gr.Blocks -> dict_interface     (datasets -> dict in RAM)
├── corpus.py          # gr.Blocks -> corpus_interface   (datasets -> SQLite FTS5)
├── tts.py             # gr.Blocks -> tts_interface      (torch.package Silero model)
├── about.py           # gr.Blocks -> links_interface    (static link buttons)
└── common.py          # shared widgets and constants
images/                # back.svg (background), logo.svg (inlined into the H1)
tests/                 # pytest, no network, no model (see conftest.py)
```

Each tab module builds its own `gr.Blocks` at **import time** and exposes it as a
module-level variable. `app.py` just collects them:

```python
demo = gr.TabbedInterface(
    [dict_interface, corpus_interface, tts_interface, links_interface],
    [dict_interface.title, corpus_interface.title, tts_interface.title, links_interface.title],
    title='TranslateKhak',
)
```

The `title=` you pass to `gr.Blocks(title="Словарь")` becomes the tab label — that is why
each module sets it.

---

## Step 1 — Create the Space

1. Create a new Space on Hugging Face with **SDK: Gradio**.
2. Put the YAML front matter at the very top of `README.md` (this file starts with it).
   Hugging Face reads it to configure the Space:

```yaml
---
title: TranslateKhak
emoji: 📚
colorFrom: green
colorTo: green
sdk: gradio
sdk_version: 6.26.0
python_version: '3.12'
app_file: app.py
pinned: false
short_description: khakas dict | corpus | tts
---
```

3. Pin your dependencies in `requirements.txt`. **Keep `gradio` here identical to
   `sdk_version` above** — otherwise the Space installs one version and runs another:

```
gradio==6.26.0
datasets
--extra-index-url https://download.pytorch.org/whl/cpu
torch==2.13.0
```

The CPU-only torch index keeps the image small and the build fast; you only need CUDA
wheels if you actually run on a GPU.

## Step 2 — Prepare the datasets

Publish your data as Hugging Face datasets and load them at import time:

```python
from datasets import load_dataset

ds = load_dataset('adeshkin/khakas-russian-dict', split='train')
```

Two datasets power this app:

- [`adeshkin/khakas-russian-dict`](https://huggingface.co/datasets/adeshkin/khakas-russian-dict) —
  columns `word` (Khakas), `semgloss` (Russian gloss), `field1` (the HTML article body).
- [`adeshkin/khakas-russian-parallel-corpus`](https://huggingface.co/datasets/adeshkin/khakas-russian-parallel-corpus) —
  columns `kjh`, `ru`.

> **Read whole columns, not rows.** `for row in ds:` is an order of magnitude slower than
> `zip(ds['word'], ds['semgloss'], ds['field1'])`, because the latter pulls the Arrow
> columns in one go. Both `corpus.py` and `kjh_ru_dict.py` do it this way.

## Step 3 — Dictionary tab

The dictionary is a plain Python dict built once at startup — `word -> [articles]`, one
map per language:

```python
word2dict_article = {'kjh': {}, 'ru': {}}
for kjh_word, ru_word, article in zip(ds['word'], ds['semgloss'], ds['field1']):
    for lang, word in (('kjh', kjh_word), ('ru', ru_word)):
        word = word.strip().lower()
        if len(word) == 0:      # entries without a gloss must not become an empty key
            continue
        word2dict_article[lang].setdefault(word, []).append(article)
```

Two details worth copying for an agglutinative language:

**Stem fallback.** Khakas glues suffixes onto stems, so `ағасха` will not be in the
dictionary while `ағас` is. `lookup_word` trims the word one character at a time and
returns the longest prefix that *is* an entry, bounded by two constants so the fallback
does not degrade into nonsense:

```python
MIN_STEM_LEN = 3        # never search shorter than this
MAX_SUFFIX_LEN = 6      # never strip more than this
```

When a stem (not the exact word) matched, the answer is prefixed with a note telling the
user which entry is being shown.

**Article clean-up.** The source articles are legacy HTML. `prepare_article()` runs a
short pipeline of pre-compiled regexes: normalise the Cyrillic-`і` tags (`<і>` → `<i>`),
split multi-sense entries onto separate lines at `;` / `:` and before numbered senses,
drop empty tags and trailing `<br>`. Compile every regex at module level — these run on
every request.

## Step 4 — Corpus tab (FTS5 full-text search)

Scanning a parallel corpus with Python string matching is far too slow. Instead the corpus
is loaded once into an **in-file SQLite FTS5 index**:

```python
CREATE_TABLE_SQL = ('CREATE VIRTUAL TABLE corpus USING fts5('
                    'kjh, ru, tokenize="unicode61 remove_diacritics 0")')
```

`remove_diacritics 0` is essential for Khakas: without it `кун` and `кӱн` would collapse
into the same token.

Key techniques in [`corpus.py`](corpus.py):

- **Cached index.** The DB file name embeds a schema version and a dataset fingerprint
  (`kjh_corpus_v1_<sha1>.db` in the temp dir). If the file exists, startup is instant; if
  the dataset or schema changes, the name changes and the index is rebuilt.
- **Atomic build.** The index is written to `<db>.<pid>.tmp` and then `os.replace()`d, so a
  concurrent worker can never read a half-built database.
- **Thread-local read-only connections.** Gradio serves requests from a thread pool, and
  SQLite connections are not shareable across threads:

  ```python
  connections = threading.local()
  con = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
  ```

- **Safe queries.** User input goes through `quote_phrase()` (wrapped in quotes, inner
  quotes doubled), so no input can break FTS5 `MATCH` syntax.
- **Fresh examples every time.** `ORDER BY RANDOM() LIMIT ?` — common words have tens of
  thousands of hits and the scan costs single-digit milliseconds.
- **Prefix fallback.** No exact hits? Retry with `word*` and tell the user that prefix
  matches are being shown.
- **Highlighting.** `highlight_word()` wraps the match in `<b>` using word-boundary
  look-arounds built from `[^\W\d_]`, which is Unicode-aware (plain `\b` misbehaves around
  Cyrillic extension letters).

## Step 5 — TTS tab

The voice model is a Silero package pulled from the Hub and loaded with
`torch.package`:

```python
model_path = hf_hub_download(repo_id='adeshkin/silero-models-v5-cis-base-nostress',
                             filename='v5_cis_base_nostress.pt')
model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
model.to(torch.device("cpu"))
```

`apply_tts()` returns a float tensor; Gradio's `gr.Audio(type="numpy")` wants
`(sample_rate, int16_array)`, so clip and scale before returning:

```python
data = np.clip(audio_tensor.squeeze().cpu().numpy(), -1.0, 1.0)
data = np.round(data * 32767).astype(np.int16)
return SAMPLE_RATE, data
```

Validate input length (`MAX_TEXT_LEN = 300`) and report problems with `gr.Warning(...)`
plus a `None` return — the user gets a toast instead of a stack trace.

**Concurrency.** Synthesis is CPU-bound and free Spaces have two cores, so TTS events are
capped while search stays parallel:

```python
submit_btn.click(fn=text_to_speech, ..., concurrency_limit=1)
```

## Step 6 — Links tab

[`about.py`](about.py) is pure data: a list of `(section, [(icon, title, description, url)])`
rendered as link buttons.

```python
with gr.Blocks(title="Ссылки") as links_interface:
    for group_title, group_links in LINK_GROUPS:
        gr.Markdown(f"### {group_title}")
        with gr.Row(equal_height=True):
            for icon, link_title, link_desc, link_url in group_links:
                gr.Button(f"{icon}  {link_title}", link=link_url, variant="secondary", size="lg")
```

`gr.Button(link=...)` renders an anchor — no callback, no server round-trip.

## Step 7 — Assemble app.py

[`app.py`](app.py) does four things:

1. **Inlines the SVG artwork into CSS.** The files in `images/` are URL-encoded and
   embedded as `data:image/svg+xml,...`, so there are no extra static-file requests:

   ```python
   def load_svg_encoded(filename):
       with open(os.path.join(image_dir, filename), encoding="utf-8") as f:
           return urllib.parse.quote(f.read())
   ```

   `back.svg` becomes a fixed background; `logo.svg` is injected via `h1::before`.

2. **Custom CSS** for larger fonts, the compact Khakas-letter keypad and the footer.
   Target your own elements with `elem_classes=` (e.g. `elem_classes="result-output"`) —
   never rely on Gradio's internal class names.

3. **Queue settings.** Search answers in fractions of a millisecond, so the default
   one-at-a-time queue would make it wait behind synthesis:

   ```python
   demo.queue(default_concurrency_limit=8)
   ```

4. **Theme and launch.**

   ```python
   THEME = gr.themes.Soft(primary_hue="green", secondary_hue="slate",
                          neutral_hue="slate", radius_size=gr.themes.sizes.radius_lg)
   demo.launch(css=CUSTOM_CSS, theme=THEME)
   ```

---

## ⚠️ ZeroGPU: the required `@spaces.GPU` stub

> **If your Space hardware is ZeroGPU, the Space will not start unless the code contains at
> least one function decorated with `@spaces.GPU`.**

ZeroGPU allocates a GPU on demand and inspects your code for `@spaces.GPU`-decorated
functions at startup. A Space that never uses the GPU — like this one, which runs on CPU —
still fails to boot on ZeroGPU hardware with no such function present. The fix is a stub
that is *never called*:

```python
import os

if os.environ.get("SPACE_ID"):
    import spaces

    @spaces.GPU
    def zerogpu_startup_check_unused() -> bool:
        """Stub required by HF Spaces: on ZeroGPU hardware the Space refuses to
        start unless the code contains at least one @spaces.GPU function. The real
        functionality does not use the GPU; this function is never called."""
        return True
```

Notes:

- Put this **at the very top of `app.py`**, before importing your tab modules.
- The `SPACE_ID` guard keeps local runs working: `spaces` is only installed on Spaces, and
  importing it locally would crash.
- Add `spaces` to `requirements.txt` when you run on ZeroGPU hardware.
- In this repository the block is present but **commented out**, because the Space runs on
  CPU Basic. Uncomment it (and add the dependency) the moment you switch the hardware to
  ZeroGPU in *Settings → Hardware*.
- If you genuinely use the GPU, decorate the real inference function instead and drop the
  stub — one decorated function is enough, and it should be the one doing GPU work.

---

## Step 8 — Tests without network or models

Every module downloads a dataset or a model *at import time*, which would make tests slow,
flaky and offline-hostile. [`conftest.py`](conftest.py) installs fakes into `sys.modules`
**before** pytest imports the test modules: a `FakeDataset` backed by a handful of
hand-written rows, a stub `torch` (including `torch.package`) and a fake `hf_hub_download`.

The fixture corpus deliberately includes the tricky cases:

- a loanword (`телефон`) that appears in *both* the Khakas and the Russian column, to test
  de-duplication;
- an entry with a blank gloss, to make sure it never becomes an empty dictionary key;
- more rows than `NUM_EXAMPLES` for one word, to test the result limit.

Dev dependencies stay minimal — no `datasets`, no `torch`:

```
gradio==6.26.0
numpy
pytest
```

```bash
pip install -r requirements-dev.txt && pytest
```

## Step 9 — CI: GitHub → Hugging Face sync

Develop on GitHub, deploy to the Space automatically. `.github/workflows/sync-to-hub.yml`
runs the tests on every push and PR, and pushes to the Hub only when the tests pass on
`master`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'
          cache: pip
          cache-dependency-path: requirements-dev.txt
      - run: pip install -r requirements-dev.txt
      - run: pytest

  sync:
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: huggingface/hub-sync@v0.1.0
        with:
          github_repo_id: ${{ github.repository }}
          huggingface_repo_id: adeshkin/translate-khakas
          hf_token: ${{ secrets.HF_TOKEN }}
```

Create an HF access token with **write** permission and store it as the repository secret
`HF_TOKEN`.

## Run locally

```bash
git clone https://github.com/adeshkin/translate-khakas-hf-space
```

```bash
cd translate-khakas-hf-space && python -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt && python app.py
```

The first run downloads the datasets and the TTS model and builds the FTS5 index; later
runs reuse the cached index and start immediately.

## Performance notes

Worth keeping in mind if you adapt this for your own language:

| Problem | Solution used here |
|---|---|
| Row-by-row dataset iteration is slow | Read Arrow columns whole: `zip(ds['kjh'], ds['ru'])` |
| Full-text search over a large corpus | SQLite FTS5 virtual table |
| Diacritics collapsing distinct letters | `tokenize="unicode61 remove_diacritics 0"` |
| Rebuilding the index on every start | Cache the DB file, name it by schema version + dataset fingerprint |
| Half-built DB read by another worker | Build into a temp file, then `os.replace()` |
| SQLite connections across Gradio threads | `threading.local()` connection per thread |
| Slow search behind slow synthesis | `demo.queue(default_concurrency_limit=8)` + `concurrency_limit=1` on TTS events |
| Rebuilding key lists for "random word" | Materialise them once at startup |
| Regex cost per request | Compile every pattern at module level |

## Project links

### Data
- 📚 [Khakas–Russian parallel corpus](https://huggingface.co/datasets/adeshkin/khakas-russian-parallel-corpus) — parallel sentence dataset on Hugging Face
- 📖 [Khakas–Russian dictionary](https://huggingface.co/datasets/adeshkin/khakas-russian-dict) — dictionary-entry dataset on Hugging Face

### Datasets and models
- 🤖 [Khakas Translation collection](https://huggingface.co/collections/adeshkin/khakas-translation) — texts, models and datasets on Hugging Face
- ⚙️ [MT training code](https://github.com/adeshkin/khakas-mt) — fine-tuning NLLB-200 and Hy-MT2

### Khakas keyboard
- 📱 [Mobile keyboard](https://yandex.ru/yandexapp/ru/keyboard/) — Yandex Keyboard with Khakas support
- 💻 [Desktop keyboard](https://dict.khakbooks.ru/keyboard) — Khakas keyboard driver for PC

### Services
- 🌐 [Yandex Translate](https://translate.yandex.ru/?source_lang=kjh&target_lang=ru) — translation from and into Khakas

### Project
- 👥 [VKontakte community](https://vk.ru/translate_khakas) — project news and updates
- ✈️ [Telegram channel](https://t.me/translate_khakas) — technical news and updates
- 🐙 [GitHub repository](https://github.com/adeshkin/translate-khakas-hf-space) — project source code

---

<div align="center">

**[🚀 Open the app → adeshkin-translate-khakas.hf.space](https://adeshkin-translate-khakas.hf.space/)**

</div>
