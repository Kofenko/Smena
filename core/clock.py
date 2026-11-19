"""Часы приложения. В обычном режиме — время телефона,
в отладочном можно сдвигать."""
from datetime import datetime, timedelta


class AppClock:
    def __init__(self):
        self.offset = timedelta()

    def now(self) -> datetime:
        return datetime.now() + self.offset

    def shift(self, delta: timedelta):
        self.offset += delta

    def set(self, target: datetime):
        self.offset = target - datetime.now()

    def reset(self):
        self.offset = timedelta()

    @property
    def fake(self) -> bool:
        return abs(self.offset.total_seconds()) > 1
