import gradio as gr
import torch
from huggingface_hub import hf_hub_download

device = torch.device("cpu")
model_path = hf_hub_download(repo_id='adeshkin/silero-models-v5-cis-base-nostress',
                             filename='v5_cis_base_nostress.pt')

model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
model.to(device)


def text_to_speech(text, speaker, sample_rate=48000, max_text_len=300):
    if len(text) == 0:
        gr.Warning("Введите текст")
        return None

    if len(text) > max_text_len:
        gr.Warning(f"Длина текста {len(text)} > {max_text_len}")
        return None

    audio_tensor = model.apply_tts(text=text,
                                   speaker='kjh_karina' if speaker == 'Карина' else 'kjh_sibday',
                                   sample_rate=sample_rate)

    audio_np = audio_tensor.squeeze().cpu().numpy()

    return sample_rate, audio_np


demo = gr.Interface(
    fn=text_to_speech,
    inputs=[
        gr.Textbox(
            label="Введите текст для озвучки",
            lines=3,
            placeholder="Чылтыстар кемни? – перініп ала сурған идінҷек."
        ),
        gr.Radio(
            choices=["Сибдей", "Карина"],
            value="Сибдей",
            label="Выберите голос"
        )
    ],
    outputs=gr.Audio(label="Результат",
                     type="numpy"),
    title="Озвучка текста на хакасском языке",
    submit_btn="Озвучить",
    clear_btn="Очистить",
)

demo.launch()
