"""Daily action statistics kept only in this server process's memory."""

from datetime import datetime
from threading import Lock
from zoneinfo import ZoneInfo

import gradio as gr

# Abakan uses the IANA Asia/Krasnoyarsk time zone.
ABAKAN_TIMEZONE = ZoneInfo("Asia/Krasnoyarsk")


class DailyUsage:
    def __init__(self):
        self._lock = Lock()
        self._day = None
        self._counts = {}
        self._last_clicks = {}

    def snapshot(self, section, *, increment=False):
        with self._lock:
            now = datetime.now(ABAKAN_TIMEZONE)
            today = now.date()
            if today != self._day:
                self._day = today
                self._counts.clear()
                self._last_clicks.clear()
            if increment:
                self._counts[section] = self._counts.get(section, 0) + 1
                self._last_clicks[section] = now
            return today, self._counts.get(section, 0), self._last_clicks.get(section)


usage = DailyUsage()


def daily_counter(section, buttons):
    """Mount inside a tab; count clicks independently of slow/failed actions."""
    labels = {
        "dictionary": "Поисков в словаре сегодня",
        "corpus": "Поисков в корпусе сегодня",
        "tts": "Запусков озвучки сегодня",
        "links": "Переходов по ссылкам сегодня",
    }
    label = labels[section]

    def render(increment=False):
        _, count, last_click = usage.snapshot(section, increment=increment)
        last_click_text = (last_click.strftime("%H:%M:%S")
                           if last_click else "-")
        return (f"**{label}: {count}**  \n"
                f"Последний: {last_click_text}")


    output = gr.Markdown(value=render, elem_classes="daily-counter")
    timer = gr.Timer(30)
    timer.tick(fn=render, outputs=output, queue=False, show_progress="hidden",
               api_visibility="private")
    gr.on(triggers=[button.click for button in buttons],
          fn=lambda: render(increment=True), outputs=output,
          queue=False, trigger_mode="multiple", show_progress="hidden",
          api_visibility="private")
    return output
