import torch
from huggingface_hub import hf_hub_download

device = torch.device("cpu")
model_path = hf_hub_download(repo_id='adeshkin/silero-models-v5-cis-base-nostress',
                             filename='v5_cis_base_nostress.pt')

model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
model.to(device)


def text_to_speech(text, speaker, sample_rate=48000):
    if len(text):
        return None

    audio_tensor = model.apply_tts(text=text,
                                   speaker='kjh_karina' if speaker == 'Карина' else 'kjh_sibday',
                                   sample_rate=sample_rate)

    audio_np = audio_tensor.squeeze().cpu().numpy()

    return sample_rate, audio_np