"""Отладочная панель (только для ПК, флаг --debug)."""
from datetime import datetime, timedelta

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput

from core.model import add_months, generate_demo
from core.ru import MONTHS_GEN, WEEKDAYS
from ui import theme as T
from ui.widgets import Lbl, Pill

DARK = [0.11, 0.11, 0.12, 1]
DARK2 = [0.2, 0.2, 0.22, 1]


class DebugPanel(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(8),
                         size_hint_x=None, width=dp(300), **kw)
        with self.canvas.before:
            Color(*DARK)
            self._bg = Rectangle()
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        self.add_widget(Lbl(text="ОТЛАДКА", bold=True, color=T.ACCENT, font_size="13sp"))
        self.time_lbl = Lbl(text="", color=T.WHITE, bold=True, font_size="22sp")
        self.date_lbl = Lbl(text="", color=T.MUTED, font_size="13sp")
        self.add_widget(self.time_lbl)
        self.add_widget(self.date_lbl)

        grid = GridLayout(cols=4, spacing=dp(6), size_hint_y=None, height=dp(3 * 38 + 12))
        steps = [("−1 мес", ("m", -1)), ("−1 д", timedelta(days=-1)), ("−1 ч", timedelta(hours=-1)),
                 ("−10 м", timedelta(minutes=-10)),
                 ("+10 м", timedelta(minutes=10)), ("+1 ч", timedelta(hours=1)),
                 ("+1 д", timedelta(days=1)), ("+1 мес", ("m", 1)),
                 ("+4 ч", timedelta(hours=4)), ("+8 ч", timedelta(hours=8)),
                 ("+12 ч", timedelta(hours=12)), ("Сейчас", None)]
        for text, step in steps:
            b = self._btn(text)
            b.bind(on_release=lambda _, s=step: self.move(s))
            grid.add_widget(b)
        self.add_widget(grid)

        self.add_widget(Lbl(text="Задать дату и время", color=T.MUTED, font_size="12sp"))
        row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        self.inp = TextInput(text="", hint_text="ГГГГ-ММ-ДД ЧЧ:ММ", multiline=False,
                             background_color=DARK2, foreground_color=T.WHITE,
                             cursor_color=T.ACCENT, hint_text_color=T.MUTED,
                             font_size="14sp", padding=(dp(8), dp(9)))
        self.inp.bind(on_text_validate=lambda *_: self.set_time())
        row.add_widget(self.inp)
        ok = self._btn("OK")
        ok.size_hint_x = None
        ok.width = dp(50)
        ok.bind(on_release=lambda *_: self.set_time())
        row.add_widget(ok)
        self.add_widget(row)

        for text, fn in (("Тестовые данные (3 мес)", self.demo),
                         ("Очистить базу", self.clear),
                         ("Показать первый запуск", self.onboarding),
                         ("Системная тема: как в Windows", self.cycle_system)):
            b = self._btn(text)
            b.size_hint_y = None
            b.height = dp(38)
            b.bind(on_release=lambda _, f=fn, bb=b: f(bb) if f == self.cycle_system else f())
            self.add_widget(b)

        self.add_widget(Lbl(text="Уведомления", color=T.MUTED, font_size="12sp"))
        self.log = Lbl(text="—", color=T.WHITE, font_size="12sp")
        self.add_widget(self.log)
        self.add_widget(BoxLayout())
        self.add_widget(Lbl(text="Время в приложении берётся отсюда.\nРеальное время: кнопка «Сейчас».",
                            color=T.MUTED, font_size="11sp"))

    def _btn(self, text):
        return Pill(text=text, bg=DARK2, fg=T.WHITE, radius=dp(8), font_size="13sp")

    @property
    def app(self):
        return App.get_running_app()

    def tick(self):
        now = self.app.clock.now()
        self.time_lbl.text = now.strftime("%H:%M:%S")
        fake = "  (сдвинуто)" if self.app.clock.fake else ""
        self.date_lbl.text = f"{now.day} {MONTHS_GEN[now.month - 1]} {now.year}, {WEEKDAYS[now.weekday()]}{fake}"

    def move(self, step):
        c = self.app.clock
        if step is None:
            c.reset()
        elif isinstance(step, tuple):
            now = c.now()
            target = datetime.combine(add_months(now.date(), step[1]), now.time())
            c.set(target)
        else:
            c.shift(step)
        self.app.after_data_change()

    def set_time(self):
        try:
            self.app.clock.set(datetime.strptime(self.inp.text.strip(), "%Y-%m-%d %H:%M"))
        except ValueError:
            self.app.toast("Формат: 2026-11-19 08:30")
            return
        self.app.after_data_change()

    def demo(self):
        generate_demo(self.app.store, self.app.clock.now())
        self.app.toast("Сгенерированы тестовые смены")
        self.app.after_data_change()

    def clear(self):
        self.app.store.clear()
        self.app.toast("База очищена")
        self.app.after_data_change()

    def onboarding(self):
        self.app.store.settings.onboarded = False
        self.app.store.save()
        self.app.show_onboarding()

    def cycle_system(self, btn):
        """Имитация темы телефона: как в Windows → светлая → тёмная."""
        order = [None, "light", "dark"]
        names = {None: "как в Windows", "light": "светлая", "dark": "тёмная"}
        nxt = order[(order.index(T.debug_system_override) + 1) % 3]
        T.debug_system_override = nxt
        btn.text = f"Системная тема: {names[nxt]}"
        self.app.update_theme()
        if self.app.sm.current == "settings":
            self.app.settings_screen.refresh()

    def notified(self, title, text):
        now = self.app.clock.now()
        self.log.text = f"{now:%d.%m %H:%M} — {title}\n{text}"
