"""Общие заглушки для тестов.

Модули приложения при импорте скачивают датасеты с Hugging Face и грузят
модель TTS. Чтобы тесты были быстрыми и работали без сети, здесь `datasets`
и `torch` подменяются заглушками, а `hf_hub_download` — фиктивной загрузкой.
Заглушки ставятся до того, как pytest импортирует тестовые модули.
"""

import hashlib
import sys
import types

import numpy as np

CORPUS_ROWS = [
    {"kjh": "Мин Ағбанда чуртапчам.", "ru": "Я живу в Абакане."},
    {"kjh": "Ол пала книга хығырча.", "ru": "Этот ребёнок читает книгу."},
    {"kjh": "Пӱӱн чылығ кӱн полған.", "ru": "Сегодня был тёплый день."},
    {"kjh": "Мин пу книга хығырчам.", "ru": "Я читаю эту книгу."},
    {"kjh": "Аның книгазы стол ӱстӱнде.", "ru": "Его книга на столе."},
    {"kjh": "Пic книга садып алғабыс.", "ru": "Мы купили книгу."},
]

DICT_ROWS = [
    {
        "word": "ағас",
        "semgloss": "дерево",
        "field1": "<b>ағас</b> <i>сущ.</i> дерево; лес",
    },
    {
        "word": "Ағас",
        "semgloss": "древесина",
        "field1": "<b>ағас</b> <i>сущ.</i> древесина",
    },
    {
        "word": "книга",
        "semgloss": "книга",
        "field1": "<b>книга</b> <i>сущ.</i> книга",
    },
]

DICT_HF_ID = "adeshkin/khakas-russian-dict"
CORPUS_HF_ID = "adeshkin/khakas-russian-parallel-corpus"


class FakeDataset:
    """Минимальная замена `datasets.Dataset`.

    Приложение читает датасет двумя способами: обходом строк и выборкой колонки
    целиком (`ds['kjh']`), поэтому заглушка поддерживает оба.
    """

    def __init__(self, rows):
        self._rows = [dict(row) for row in rows]

    def __len__(self):
        return len(self._rows)

    def __iter__(self):
        return iter(self._rows)

    def __getitem__(self, key):
        if isinstance(key, str):
            return [row[key] for row in self._rows]

        return self._rows[key]

    @property
    def _fingerprint(self):
        return hashlib.sha1(repr(self._rows).encode()).hexdigest()[:16]


def _load_dataset(path, split=None, **kwargs):
    if path == DICT_HF_ID:
        return FakeDataset(DICT_ROWS)
    if path == CORPUS_HF_ID:
        return FakeDataset(CORPUS_ROWS)
    raise AssertionError(f"Неизвестный датасет в тестах: {path}")


def _install_datasets_stub():
    stub = types.ModuleType("datasets")
    stub.load_dataset = _load_dataset
    sys.modules["datasets"] = stub


class FakeAudioTensor:
    """Минимальная замена torch-тензора для `apply_tts`."""

    def __init__(self, data):
        self._data = np.asarray(data, dtype=np.float32)

    def squeeze(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self._data


class FakeTTSModel:
    """Модель TTS: запоминает вызовы и отдаёт предсказуемый сигнал."""

    #: значения подобраны так, чтобы проверялись и обрезка, и масштабирование
    WAVEFORM = [-1.5, -1.0, 0.0, 0.5, 1.0, 1.5]

    def __init__(self):
        self.device = None
        self.calls = []

    def to(self, device):
        self.device = device
        return self

    def apply_tts(self, text, speaker, sample_rate):
        self.calls.append({"text": text, "speaker": speaker, "sample_rate": sample_rate})
        return FakeAudioTensor(self.WAVEFORM)


def _install_torch_stub():
    torch_stub = types.ModuleType("torch")
    torch_stub.device = lambda name: f"device({name})"

    package_stub = types.ModuleType("torch.package")

    class PackageImporter:
        def __init__(self, path):
            self.path = path

        def load_pickle(self, package, resource):
            model = FakeTTSModel()
            model.loaded_from = (self.path, package, resource)
            return model

    package_stub.PackageImporter = PackageImporter
    torch_stub.package = package_stub

    sys.modules["torch"] = torch_stub
    sys.modules["torch.package"] = package_stub


def _install_hf_hub_stub():
    import huggingface_hub

    huggingface_hub.hf_hub_download = lambda repo_id, filename, **kwargs: (
        f"/fake-hub/{repo_id}/{filename}"
    )


_install_datasets_stub()
_install_torch_stub()
_install_hf_hub_stub()
