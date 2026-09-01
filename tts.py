import torch
from huggingface_hub import hf_hub_download
import gradio as gr
import random
import numpy as np

from corpus import get_random_kjh_example

device = torch.device("cpu")
model_path = hf_hub_download(repo_id='adeshkin/silero-models-v5-cis-base-nostress',
                             filename='v5_cis_base_nostress.pt')
model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
model.to(device)

SAMPLE_RATE = 48000
MAX_TEXT_LEN = 300
SPEAKER2MODEL_SPEAKER = {'Карина': 'kjh_karina',
                         'Сибдей': 'kjh_sibday'}


def text_to_speech(text, speaker):
    text = text.strip().lower()
    if len(text) == 0:
        gr.Warning("Введите текст")
        return None

    if len(text) > MAX_TEXT_LEN:
        gr.Warning(f"Длина текста {len(text)} > {MAX_TEXT_LEN}")
        return None

    model_speaker = SPEAKER2MODEL_SPEAKER.get(speaker, None)
    if model_speaker is None:
        gr.Warning(
            f"Speaker {speaker} не поддерживается, только {SPEAKER2MODEL_SPEAKER.keys()}")
        return None

    audio_tensor = model.apply_tts(text=text,
                                   speaker=model_speaker,
                                   sample_rate=SAMPLE_RATE)

    data = audio_tensor.squeeze().cpu().numpy()
    data = np.clip(data, -1.0, 1.0)
    data = np.round(data * 32767).astype(np.int16)

    return SAMPLE_RATE, data


def random_text_to_speech():
    speaker = random.choice(list(SPEAKER2MODEL_SPEAKER.keys()))
    sent = get_random_kjh_example(MAX_TEXT_LEN)

    return sent, speaker, text_to_speech(sent, speaker)


def insert_letter(letter):
    def _insert(text):
        return (text or "") + letter

    return _insert


with gr.Blocks(title="Озвучка") as tts_interface:
    gr.Markdown("Озвучка")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Текст",
                placeholder="Введите текст"
            )
            with gr.Row(elem_classes="khakas-letters"):
                for letter in "іғңҷӧӱ":
                    letter_btn = gr.Button(letter, size="sm", scale=0)
                    letter_btn.click(insert_letter(letter), inputs=text_input, outputs=text_input)

            speaker_input = gr.Radio(
                choices=["Сибдей", "Карина"],
                value="Сибдей",
                label="Голос"
            )
            with gr.Row():
                submit_btn = gr.Button("Озвучить", variant="primary")
                random_btn = gr.Button("Случайное предложение")
                clear_btn = gr.Button("Очистить")

        with gr.Column():
            audio_output = gr.Audio(label="Результат", type="numpy")

    # Синтез упирается в CPU, а ядер всего два: больше одного за раз не запускаем.
    submit_btn.click(fn=text_to_speech,
                     inputs=[text_input, speaker_input],
                     outputs=audio_output,
                     concurrency_limit=1)
    random_btn.click(fn=random_text_to_speech,
                     inputs=None,
                     outputs=[text_input, speaker_input, audio_output],
                     concurrency_limit=1)
    clear_btn.click(fn=lambda: ("", "Сибдей", None),
                    inputs=None,
                    outputs=[text_input, speaker_input, audio_output])
