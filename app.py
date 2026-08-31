import gradio as gr
from tts import text_to_speech

demo = gr.Interface(
    fn=text_to_speech,
    inputs=[
        gr.Textbox(
            label="Введите текст для озвучки",
            # lines=3,
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
