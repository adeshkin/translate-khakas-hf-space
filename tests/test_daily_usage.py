from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import daily_usage


def test_counts_are_shared_and_sections_independent():
    counter = daily_usage.DailyUsage()
    assert counter.snapshot("dictionary", increment=True)[1] == 1
    assert counter.snapshot("dictionary")[1] == 1
    assert counter.snapshot("corpus")[1] == 0
    assert counter.snapshot("dictionary")[2] is not None
    assert counter.snapshot("corpus")[2] is None


def test_resets_all_sections_at_abakan_midnight(monkeypatch):
    class Clock:
        now_utc = datetime(2026, 9, 7, 16, 59, 59, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz):
            return cls.now_utc.astimezone(tz)

    monkeypatch.setattr(daily_usage, "datetime", Clock)
    counter = daily_usage.DailyUsage()
    for section in ("dictionary", "corpus", "tts", "links"):
        counter.snapshot(section, increment=True)
    Clock.now_utc = datetime(2026, 9, 7, 17, tzinfo=timezone.utc)
    for section in ("dictionary", "corpus", "tts", "links"):
        day, count, last_click = counter.snapshot(section)
        assert str(day) == "2026-09-08"
        assert count == 0
        assert last_click is None
    assert counter.snapshot("links", increment=True)[1] == 1


def test_concurrent_clicks_are_not_lost():
    counter = daily_usage.DailyUsage()
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: counter.snapshot("tts", increment=True), range(1000)))
    assert counter.snapshot("tts")[1] == 1000


def test_counts_do_not_survive_recreating_counter():
    counter = daily_usage.DailyUsage()
    counter.snapshot("dictionary", increment=True)
    restarted = daily_usage.DailyUsage()
    assert restarted.snapshot("dictionary")[1:] == (0, None)


def test_last_click_uses_abakan_time_and_is_independent(monkeypatch):
    class Clock:
        now_utc = datetime(2026, 9, 7, 10, 20, 30, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz):
            return cls.now_utc.astimezone(tz)

    monkeypatch.setattr(daily_usage, "datetime", Clock)
    counter = daily_usage.DailyUsage()
    last_click = counter.snapshot("tts", increment=True)[2]

    assert last_click.strftime("%H:%M:%S") == "17:20:30"
    assert counter.snapshot("dictionary")[2] is None
