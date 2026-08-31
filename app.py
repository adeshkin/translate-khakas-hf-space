import gradio as gr

from kjh_ru_dict import dict_interface
from corpus import corpus_interface
from tts import tts_interface

demo = gr.TabbedInterface([dict_interface, corpus_interface, tts_interface],
                          [dict_interface.title, corpus_interface.title, tts_interface.title],
                          title='TranslateKhak')
demo.launch()
