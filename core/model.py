"""Хранилище смен (JSON) и все расчёты. Без зависимостей от Kivy —
используется и приложением, и фоновым сервисом уведомлений."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

FMT = "%Y-%m-%dT%H:%M"
NIGHT_START = time(22, 30)   # смена, идущая в 22:30 или начатая позже, — ночная
NIGHT_END = time(6, 0)       # начало смены до 06:00 тоже считается ночным
ALERT_HOURS = (8, 12)


def parse(s: str) -> datetime:
    return datetime.strptime(s, FMT)


def fmt(dt: datetime) -> str:
    return dt.strftime(FMT)


def trunc(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def hhmm(minutes: int) -> str:
    h, m = divmod(max(0, int(minutes)), 60)
    return f"{h:02d}:{m:02d}"


def add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    last = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
    return d.replace(year=y, month=m, day=min(d.day, last))


def split_by_day(start: datetime, end: datetime) -> dict[date, int]:
    """Минуты смены, разложенные по календарным дням."""
    res: dict[date, int] = {}
    cur = start
    while cur < end:
        nxt = datetime.combine(cur.date() + timedelta(days=1), time())
        seg = min(nxt, end)
        res[cur.date()] = res.get(cur.date(), 0) + int((seg - cur).total_seconds() // 60)
        cur = seg
    return res


def days_touched(start: datetime, end: datetime) -> list[date]:
    days = [start.date()]
    last = (end - timedelta(minutes=1)).date() if end > start else start.date()
    d = start.date()
    while d < last:
        d += timedelta(days=1)
        days.append(d)
    return days


def is_night(start: datetime, end: datetime) -> bool:
    t = start.time()
    if t >= NIGHT_START or t < NIGHT_END:
        return True
    # смена уже идёт в 22:30
    return datetime.combine(start.date(), NIGHT_START) < end


@dataclass
class Shift:
    start: datetime
    end: datetime | None = None   # None — смена ещё идёт
    index: int = -1               # позиция в списке (-1 у открытой)

    def end_at(self, now: datetime) -> datetime:
        return self.end if self.end else max(now, self.start)

    def minutes(self, now: datetime) -> int:
        return int((self.end_at(now) - self.start).total_seconds() // 60)

    def night(self, now: datetime) -> bool:
        return is_night(self.start, self.end_at(now))


@dataclass
class DayInfo:
    day: date
    minutes: int = 0
    night: bool = False
    shifts: list[Shift] = field(default_factory=list)


@dataclass
class Settings:
    rate: float = 0.0          # € в час
    notify: bool = True
    onboarded: bool = False
    theme: str = "system"      # system / light / dark


class Store:
    def __init__(self, folder: str):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)
        self.path = os.path.join(folder, "data.json")
        self.notified_path = os.path.join(folder, "notified.json")
        self.settings = Settings()
        self.open_start: datetime | None = None
        self.shifts: list[Shift] = []
        self.load()

    # ---------- файл ----------
    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):
            return
        s = raw.get("settings", {})
        self.settings = Settings(float(s.get("rate", 0) or 0),
                                 bool(s.get("notify", True)),
                                 bool(s.get("onboarded", False)),
                                 s.get("theme", "system") if s.get("theme") in ("system", "light", "dark") else "system")
        self.open_start = parse(raw["open"]) if raw.get("open") else None
        self.shifts = [Shift(parse(x["start"]), parse(x["end"]))
                       for x in raw.get("shifts", [])]
        self._reindex()

    def save(self):
        raw = {
            "version": 1,
            "settings": vars(self.settings),
            "open": fmt(self.open_start) if self.open_start else None,
            "shifts": [{"start": fmt(s.start), "end": fmt(s.end)} for s in self.shifts],
        }
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)

    def _reindex(self):
        self.shifts.sort(key=lambda s: s.start)
        for i, s in enumerate(self.shifts):
            s.index = i

    # ---------- действия ----------
    def check_in(self, now: datetime):
        if self.open_start is None:
            self.open_start = trunc(now)
            self.save()

    def check_out(self, now: datetime) -> Shift | None:
        if self.open_start is None:
            return None
        sh = Shift(self.open_start, max(trunc(now), self.open_start))
        self.shifts.append(sh)
        self.open_start = None
        self._reindex()
        self.save()
        return sh

    def delete(self, shift: Shift):
        if shift.end is None:
            self.open_start = None
        elif 0 <= shift.index < len(self.shifts):
            self.shifts.pop(shift.index)
            self._reindex()
        self.save()

    def clear(self):
        self.open_start = None
        self.shifts = []
        self.save()
        if os.path.exists(self.notified_path):
            os.remove(self.notified_path)

    # ---------- расчёты ----------
    def open_shift(self) -> Shift | None:
        return Shift(self.open_start) if self.open_start else None

    def all_shifts(self) -> list[Shift]:
        o = self.open_shift()
        return self.shifts + ([o] if o else [])

    def day_map(self, now: datetime) -> dict[date, DayInfo]:
        res: dict[date, DayInfo] = {}
        for sh in self.all_shifts():
            end = sh.end_at(now)
            night = is_night(sh.start, end)
            for d in days_touched(sh.start, end):
                info = res.setdefault(d, DayInfo(d))
                info.shifts.append(sh)
                info.night |= night
            for d, m in split_by_day(sh.start, end).items():
                res.setdefault(d, DayInfo(d)).minutes += m
        return res

    def month_summary(self, year: int, month: int, now: datetime,
                      dm: dict[date, DayInfo] | None = None) -> dict:
        dm = dm if dm is not None else self.day_map(now)
        minutes = days = 0
        for d, info in dm.items():
            if d.year == year and d.month == month:
                minutes += info.minutes
                days += info.minutes > 0
        shifts = sum(1 for s in self.all_shifts()
                     if s.start.year == year and s.start.month == month)
        return {"minutes": minutes, "days": days, "shifts": shifts,
                "money": minutes / 60 * self.settings.rate}

    # ---------- уведомления ----------
    def notified(self) -> dict:
        try:
            with open(self.notified_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def mark_notified(self, start: datetime, hours: int):
        data = self.notified()
        data.setdefault(fmt(start), [])
        if hours not in data[fmt(start)]:
            data[fmt(start)].append(hours)
        with open(self.notified_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def due_alerts(self, now: datetime) -> list[int]:
        """Пороги (8/12 ч), уведомление о которых пора отправить."""
        if not self.settings.notify or self.open_start is None:
            return []
        done = self.notified().get(fmt(self.open_start), [])
        mins = (now - self.open_start).total_seconds() / 60
        due = [h for h in ALERT_HOURS if mins >= h * 60 and h not in done]
        return due[-1:]  # если пропустили оба порога — шлём только последний


def alert_text(hours: int, start: datetime) -> tuple[str, str]:
    if hours >= 12:
        return ("Уже 12 часов на работе",
                f"Смена идёт с {start:%H:%M}. Не забудь нажать «Ушёл».")
    return ("8 часов позади",
            f"Смена идёт с {start:%H:%M}. Полный рабочий день отработан.")


def generate_demo(store: Store, now: datetime, months: int = 3, seed: int = 7):
    """Тестовые данные: будни, иногда обед, иногда ночные смены."""
    import random
    rnd = random.Random(seed)
    store.shifts = []
    store.open_start = None
    d = add_months(now.date().replace(day=1), -months)
    busy_until = datetime.min
    while d < now.date():
        if datetime.combine(d, time(12)) < busy_until:  # отсыпаемся после ночной
            d += timedelta(days=1)
            continue
        wd = d.weekday()
        r = rnd.random()
        if wd < 5 and r < 0.85:
            if r < 0.12:      # ночная 22:45 → ~07:00
                st = datetime.combine(d, time(22, 30)) + timedelta(minutes=rnd.randint(0, 40))
                en = st + timedelta(minutes=rnd.randint(7 * 60, 9 * 60))
                store.shifts.append(Shift(st, en))
                busy_until = en + timedelta(hours=8)
            elif r < 0.35:    # две смены с перерывом
                st = datetime.combine(d, time(8)) + timedelta(minutes=rnd.randint(-20, 20))
                mid = st + timedelta(minutes=rnd.randint(200, 260))
                st2 = mid + timedelta(minutes=rnd.randint(30, 60))
                store.shifts += [Shift(st, mid), Shift(st2, st2 + timedelta(minutes=rnd.randint(180, 260)))]
            else:
                st = datetime.combine(d, time(8)) + timedelta(minutes=rnd.randint(-25, 30))
                store.shifts.append(Shift(st, st + timedelta(minutes=rnd.randint(450, 560))))
        elif wd == 5 and r < 0.2:
            st = datetime.combine(d, time(10))
            store.shifts.append(Shift(st, st + timedelta(minutes=rnd.randint(200, 320))))
        d += timedelta(days=1)
    store.shifts = [s for s in store.shifts if s.end <= now]
    store._reindex()
    store.save()
