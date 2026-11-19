from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import sp
from kivy.uix.screenmanager import Screen

from core.model import hhmm
from core.ru import MONTHS, MONTHS_GEN, days_word, money, num, shifts_word
from ui import theme as T

Builder.load_string("""
#:import T ui.theme
#:import dp kivy.metrics.dp

<HomeScreen>:
    name: 'home'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(24), dp(22), dp(24), dp(18)
        spacing: dp(2)
        Lbl:
            id: month
            color: T.ACCENT
            bold: True
            font_size: '15sp'
        Lbl:
            id: total
            text: '00:00'
            bold: True
            font_size: '72sp'
        Lbl:
            id: total_min
            color: T.MUTED
            font_size: '16sp'
        Widget:
            size_hint_y: None
            height: dp(10)
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            spacing: dp(8)
            Chip:
                id: money
            Chip:
                id: shifts
                bg: T.soft(T.TEXT, 0.06)
                fg: T.TEXT
            Chip:
                id: days
                bg: T.soft(T.TEXT, 0.06)
                fg: T.TEXT
            Widget
        Widget
        Lbl:
            id: status
            halign: 'center'
            color: T.MUTED
            font_size: '15sp'
        Lbl:
            id: timer
            markup: True
            halign: 'center'
            bold: True
            font_size: '40sp'
        Widget:
            size_hint_y: None
            height: dp(14)
        AnchorLayout:
            size_hint_y: None
            height: dp(230)
            BigButton:
                id: btn
                size_hint: None, None
                size: dp(230), dp(230)
                d: dp(230)
                on_release: root.toggle()
        Widget
        Card:
            id: last
            height: dp(68)
            padding: dp(18), dp(10)
            orientation: 'vertical'
            Lbl:
                id: last_title
                color: T.MUTED
                font_size: '13sp'
            Lbl:
                id: last_value
                bold: True
                font_size: '18sp'
""")


class HomeScreen(Screen):
    _working = None

    def toggle(self):
        App.get_running_app().toggle_shift()

    def refresh(self):
        app = App.get_running_app()
        store, now = app.store, app.clock.now()
        s = store.month_summary(now.year, now.month, now)
        ids = self.ids
        ids.month.text = f"{MONTHS[now.month - 1]} {now.year}".upper()
        ids.total.text = hhmm(s["minutes"])
        ids.total_min.text = f"{num(s['minutes'])} мин за месяц"
        ids.money.text = f"≈ {money(s['money'])}" if store.settings.rate > 0 else ""
        ids.shifts.text = shifts_word(s["shifts"])
        ids.days.text = days_word(s["days"])

        op = store.open_shift()
        working = op is not None
        if working:
            m = op.minutes(now)
            ids.status.text = f"На работе с {op.start:%H:%M}"
            ids.timer.text = f"{hhmm(m)}[size={int(sp(18))}][color={T.hex_of(T.MUTED)}]   {num(m)} мин[/color][/size]"
        else:
            ids.status.text = "Сейчас не на работе"
            ids.timer.text = ""
        if working != self._working:
            self._working = working
            ids.btn.text = "Ушёл" if working else "Пришёл"
            ids.btn.set_tone(T.ACCENT if working else T.GREEN)

        last = store.shifts[-1] if store.shifts else None
        if last:
            d = last.start
            ids.last_title.text = f"Последняя смена · {d.day} {MONTHS_GEN[d.month - 1]}, {last.start:%H:%M}–{last.end:%H:%M}"
            ids.last_value.text = f"{hhmm(last.minutes(now))}  ({num(last.minutes(now))} мин)"
            ids.last.opacity = 1
        else:
            ids.last.opacity = 0
