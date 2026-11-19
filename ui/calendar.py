"""Календарь: обзор года (как на iPhone) → месяц → день."""
import calendar as pycal
from datetime import date

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.widget import Widget

from core.model import add_months, hhmm
from core.ru import (MONTHS, MONTHS_GEN, WD_SHORT, WEEKDAYS, days_word, money,
                     num, shifts_word)
from ui import theme as T
from ui.widgets import Card, Chip, Lbl, Pill, text_texture

Builder.load_string("""
#:import T ui.theme
#:import dp kivy.metrics.dp

<YearView>:
    name: 'year'
    BoxLayout:
        orientation: 'vertical'
        ScrollView:
            id: sv
            do_scroll_x: False
            bar_width: 0
            BoxLayout:
                id: col
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(18), dp(8), dp(18), dp(24)
                spacing: dp(6)

<LinkBtn@ButtonBehavior+Label>:
    color: T.ACCENT if self.state == 'normal' else T.soft(T.ACCENT, 0.5)
    font_size: '18sp'
    size_hint_x: None
    width: self.texture_size[0] + dp(16)

<MonthView>:
    name: 'month'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(14), dp(6), dp(14), dp(12)
        spacing: dp(4)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            LinkBtn:
                text: '‹ ' + str(root.year)
                on_release: root.back()
            Widget
            LinkBtn:
                text: '‹'
                font_size: '30sp'
                on_release: root.move(-1)
            LinkBtn:
                text: '›'
                font_size: '30sp'
                on_release: root.move(1)
        Lbl:
            id: title
            bold: True
            font_size: '32sp'
            padding: dp(4), 0
        Lbl:
            id: sum1
            bold: True
            font_size: '18sp'
            padding: dp(4), 0
        Lbl:
            id: sum2
            color: T.MUTED
            font_size: '14sp'
            padding: dp(4), 0
        Widget:
            size_hint_y: None
            height: dp(10)
        GridLayout:
            id: wd
            cols: 7
            size_hint_y: None
            height: dp(24)
        Widget:
            size_hint_y: None
            height: dp(1)
            canvas:
                Color:
                    rgba: T.LINE
                Rectangle:
                    pos: self.pos
                    size: self.size
        MonthGrid:
            id: grid
            cols: 7
            size_hint_y: None
            height: dp(6 * 60)
        Widget
        BoxLayout:
            size_hint_y: None
            height: dp(24)
            spacing: dp(6)
            padding: dp(6), 0
            Dot:
                tone: T.soft(T.ACCENT, 0.45)
            Lbl:
                text: 'работа'
                size_hint_y: 1
                color: T.MUTED
                font_size: '13sp'
                size_hint_x: None
                width: dp(60)
            Dot:
                tone: T.NIGHT
            Lbl:
                text: 'ночная смена'
                size_hint_y: 1
                color: T.MUTED
                font_size: '13sp'
""")


class Dot(Widget):
    tone = ObjectProperty(T.ACCENT)

    def __init__(self, **kw):
        super().__init__(size_hint=(None, None), size=(dp(10), dp(24)), **kw)
        self.bind(pos=self.draw, size=self.draw, tone=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*self.tone)
            Ellipse(pos=(self.x, self.center_y - dp(5)), size=(dp(10), dp(10)))


def draw_text(t, cx, cy):
    Rectangle(texture=t, size=t.size, pos=(cx - t.width / 2, cy - t.height / 2))


# ---------------- год ----------------

class MiniMonth(ButtonBehavior, Widget):
    def __init__(self, year, month, **kw):
        super().__init__(size_hint_y=None, **kw)
        self.year, self.month = year, month
        self.dm, self.today = {}, date.today()
        self._t = Clock.create_trigger(self.redraw)
        self.bind(pos=self._t, size=self._t, width=self._h)

    def _h(self, *_):
        self.height = self.width * 1.08

    def set_data(self, dm, today):
        self.dm, self.today = dm, today
        self._t()

    def redraw(self, *_):
        self.canvas.clear()
        if self.width < 20:
            return
        cur = (self.year, self.month) == (self.today.year, self.today.month)
        title_h = sp(24)
        cw = self.width / 7
        ch = (self.height - title_h) / 6
        r = min(cw, ch) * 0.47
        with self.canvas:
            t = text_texture(MONTHS[self.month - 1], sp(14), T.ACCENT if cur else T.TEXT, True)
            Rectangle(texture=t, size=t.size, pos=(self.x + dp(2), self.top - title_h + (title_h - t.height) / 2))
            first_wd, ndays = pycal.monthrange(self.year, self.month)
            for day in range(1, ndays + 1):
                i = first_wd + day - 1
                row, colm = divmod(i, 7)
                cx = self.x + cw * (colm + 0.5)
                cy = self.top - title_h - ch * (row + 0.5)
                d = date(self.year, self.month, day)
                info = self.dm.get(d)
                worked = info is not None and info.minutes > 0
                is_today = d == self.today
                color = T.TEXT
                if is_today:
                    Color(*T.ACCENT)
                    Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
                    color = T.WHITE
                elif worked:
                    Color(*(T.soft(T.NIGHT, 0.22) if info.night else T.soft(T.ACCENT, 0.2)))
                    Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
                    color = T.NIGHT if info.night else T.ACCENT
                Color(1, 1, 1, 1)
                draw_text(text_texture(str(day), sp(9), color, worked or is_today), cx, cy)


class YearView(Screen):
    years = ()

    def refresh(self, dm, today):
        first = min([d.year for d in dm] + [today.year]) - 1
        years = tuple(range(first, today.year + 2))
        if years != self.years:
            self.build(years)
            self.scroll_to_year(today.year)
        for m in self.minis:
            m.set_data(dm, today)

    def build(self, years):
        self.years = years
        col = self.ids.col
        col.clear_widgets()
        self.minis, self.heads = [], {}
        today = App.get_running_app().clock.now().date()
        for y in years:
            head = Lbl(text=str(y), bold=True, font_size="30sp",
                       color=T.ACCENT if y == today.year else T.TEXT)
            head.padding = (0, dp(10))
            self.heads[y] = head
            col.add_widget(head)
            line = Widget(size_hint_y=None, height=dp(1))
            with line.canvas:
                Color(*T.LINE)
                rect = Rectangle()
            line.bind(pos=lambda w, *_, r=rect: setattr(r, "pos", w.pos),
                      size=lambda w, *_, r=rect: setattr(r, "size", w.size))
            col.add_widget(line)
            grid = GridLayout(cols=3, spacing=(dp(14), dp(14)), size_hint_y=None,
                              padding=(0, dp(10)))
            grid.bind(minimum_height=grid.setter("height"))
            for m in range(1, 13):
                mm = MiniMonth(y, m)
                mm.bind(on_release=lambda w: self.open_month(w.year, w.month))
                self.minis.append(mm)
                grid.add_widget(mm)
            col.add_widget(grid)

    def on_kv_post(self, *_):
        self._pending = None
        self.ids.col.bind(height=self._relayout)
        self.ids.sv.bind(on_scroll_start=lambda *_: setattr(self, "_pending", None))

    def _relayout(self, *_):
        if self._pending:
            Clock.schedule_once(lambda *_: self._apply_scroll(), 0)

    def scroll_to_year(self, y):
        """Прокрутить к году; повторяется, пока вёрстка ещё досчитывается."""
        self._pending = y
        Clock.schedule_once(lambda *_: self._apply_scroll(), 0)
        Clock.schedule_once(lambda *_: setattr(self, "_pending", None), 1.0)

    def _apply_scroll(self):
        y = self._pending
        sv, col = self.ids.sv, self.ids.col
        if y not in self.heads or col.height <= sv.height:
            return
        head = self.heads[y]
        dist = col.top - head.top - dp(4)
        sv.scroll_y = max(0.0, min(1.0, 1 - dist / (col.height - sv.height)))

    def open_month(self, y, m):
        self.manager.parent_screen.open_month(y, m)


# ---------------- месяц ----------------

class DayCell(ButtonBehavior, Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.day, self.info, self.today = None, None, None
        self._t = Clock.create_trigger(self.redraw)
        self.bind(pos=self._t, size=self._t, state=self._t)

    def set(self, day, info, today):
        self.day, self.info, self.today = day, info, today
        self.disabled = day is None
        self._t()

    def redraw(self, *_):
        self.canvas.clear()
        if self.day is None:
            return
        info = self.info
        worked = info is not None and info.minutes > 0
        is_today = self.day == self.today
        cx = self.center_x
        cy = self.y + self.height * 0.6
        r = min(self.width, self.height) * 0.3
        with self.canvas:
            if self.state == "down":
                Color(*T.soft(T.TEXT, 0.06))
                RoundedRectangle(pos=(self.x + dp(2), self.y + dp(2)),
                                 size=(self.width - dp(4), self.height - dp(4)), radius=[dp(10)])
            color = T.TEXT
            if worked:
                Color(*(T.soft(T.NIGHT, 0.2) if info.night else T.soft(T.ACCENT, 0.16)))
                Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
                color = T.NIGHT if info.night else T.ACCENT
            if is_today:
                Color(*T.ACCENT)
                Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
                color = T.WHITE
            Color(1, 1, 1, 1)
            draw_text(text_texture(str(self.day.day), sp(17), color, worked or is_today), cx, cy)
            if worked:
                sub = text_texture(hhmm(info.minutes), sp(10.5),
                                   T.NIGHT if info.night else T.MUTED, info.night)
                draw_text(sub, cx, self.y + self.height * 0.14)
            elif info is not None and info.shifts:  # смена идёт, 0 минут
                Color(*T.ACCENT)
                Ellipse(pos=(cx - dp(2.5), self.y + self.height * 0.14 - dp(2.5)), size=(dp(5), dp(5)))


class MonthGrid(GridLayout):
    """Сетка дней со свайпом влево/вправо."""
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.ud["swipe_x"] = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        sx = touch.ud.get("swipe_x")
        if sx is not None and abs(touch.x - sx) > dp(60):
            touch.ud["swipe_x"] = None
            mv = self.parent
            while not isinstance(mv, MonthView):
                mv = mv.parent
            Clock.schedule_once(lambda *_: mv.move(-1 if touch.x > sx else 1), 0)
            for c in self.children:
                c.state = "normal"
            return True
        return super().on_touch_up(touch)


class MonthView(Screen):
    year = NumericProperty(2026)
    month = NumericProperty(1)

    def on_kv_post(self, *_):
        for w in WD_SHORT:
            self.ids.wd.add_widget(Lbl(text=w, halign="center", font_size="12sp",
                                       color=T.MUTED, size_hint_y=None, height=dp(24)))
        self.cells = []
        for _ in range(42):
            c = DayCell()
            c.bind(on_release=self.open_day)
            self.cells.append(c)
            self.ids.grid.add_widget(c)

    def show(self, y, m):
        self.year, self.month = y, m
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        now = app.clock.now()
        dm = app.store.day_map(now)
        s = app.store.month_summary(self.year, self.month, now, dm)
        self.ids.title.text = MONTHS[self.month - 1]
        self.ids.sum1.text = f"{hhmm(s['minutes'])}  ·  {num(s['minutes'])} мин"
        parts = [shifts_word(s["shifts"]), days_word(s["days"])]
        if app.store.settings.rate > 0:
            parts.append(f"≈ {money(s['money'])}")
        self.ids.sum2.text = "  ·  ".join(parts)
        first_wd, ndays = pycal.monthrange(self.year, self.month)
        for i, c in enumerate(self.cells):
            n = i - first_wd + 1
            if 1 <= n <= ndays:
                d = date(self.year, self.month, n)
                c.set(d, dm.get(d), now.date())
            else:
                c.set(None, None, None)

    def move(self, step):
        d = add_months(date(self.year, self.month, 1), step)
        self.show(d.year, d.month)

    def back(self):
        self.manager.parent_screen.show_year()

    def open_day(self, cell):
        if cell.day:
            DaySheet(cell.day, on_change=self.refresh).open()


# ---------------- день ----------------

class DaySheet(ModalView):
    def __init__(self, day, on_change, **kw):
        phone = App.get_running_app().phone
        super().__init__(size_hint=(None, None), width=phone.width, pos_hint={"x": 0, "y": 0},
                         background_color=(0, 0, 0, 0), overlay_color=(0, 0, 0, 0.3), **kw)
        self.day, self.on_change = day, on_change
        self.build()

    def build(self):
        self.clear_widgets()
        app = App.get_running_app()
        now = app.clock.now()
        info = app.store.day_map(now).get(self.day)
        box = Card(orientation="vertical", padding=(dp(22), dp(14), dp(22), dp(24)),
                   spacing=dp(6), size_hint_y=None, radius=dp(22))

        grab = Widget(size_hint_y=None, height=dp(10))
        with grab.canvas:
            Color(*T.LINE)
            gr = RoundedRectangle(radius=[dp(2.5)])
        grab.bind(pos=lambda w, *_: setattr(gr, "pos", (w.center_x - dp(18), w.center_y)),
                  size=lambda w, *_: setattr(gr, "size", (dp(36), dp(5))))
        box.add_widget(grab)

        wd = WEEKDAYS[self.day.weekday()]
        box.add_widget(Lbl(text=f"{self.day.day} {MONTHS_GEN[self.day.month - 1]}, {wd}",
                           color=T.MUTED, font_size="15sp"))
        mins = info.minutes if info else 0
        box.add_widget(Lbl(text=hhmm(mins), bold=True, font_size="46sp"))
        box.add_widget(Lbl(text=f"{num(mins)} мин", color=T.MUTED, font_size="15sp"))

        chips = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8), padding=(0, dp(6), 0, 0))
        if info and info.shifts:
            chips.add_widget(Chip(text=shifts_word(len(info.shifts)),
                                  bg=T.soft(T.TEXT, 0.06), fg=T.TEXT))
            if info.night:
                chips.add_widget(Chip(text="Ночная смена", bg=T.soft(T.NIGHT, 0.14), fg=T.NIGHT))
            if app.store.settings.rate > 0:
                chips.add_widget(Chip(text=f"≈ {money(mins / 60 * app.store.settings.rate)}"))
        chips.add_widget(Widget())
        box.add_widget(chips)

        if not info or not info.shifts:
            box.add_widget(Lbl(text="В этот день смен не было", color=T.MUTED,
                               padding=(0, dp(14))))
        else:
            box.add_widget(Widget(size_hint_y=None, height=dp(6)))
            for sh in info.shifts:
                box.add_widget(self.shift_row(sh, now))

        box.bind(minimum_height=box.setter("height"))
        outer = BoxLayout(padding=dp(8))
        outer.add_widget(box)
        self.add_widget(outer)
        box.bind(height=lambda *_: setattr(self, "height", box.height + dp(16)))
        self.height = box.minimum_height + dp(16)

    def shift_row(self, sh, now):
        end = sh.end_at(now)
        right = "сейчас" if sh.end is None else f"{end:%H:%M}"
        if sh.end is not None and end.date() != sh.start.date():
            right += f" ({end.day} {MONTHS_GEN[end.month - 1][:3]})"
        if sh.start.date() != self.day:
            left = f"{sh.start:%H:%M} ({sh.start.day} {MONTHS_GEN[sh.start.month - 1][:3]})"
        else:
            left = f"{sh.start:%H:%M}"
        row = Card(size_hint_y=None, height=dp(56), padding=(dp(14), dp(8)), spacing=dp(8),
                   bg=T.BG, radius=dp(12))
        col = BoxLayout(orientation="vertical")
        col.add_widget(Lbl(text=f"{left} – {right}", font_size="15sp", bold=True))
        night = " · ночная" if sh.night(now) else ""
        col.add_widget(Lbl(text=f"{hhmm(sh.minutes(now))} ({num(sh.minutes(now))} мин){night}",
                           color=T.MUTED, font_size="13sp"))
        row.add_widget(col)
        btn = Pill(text="Удалить", bg=T.soft(T.ACCENT, 0.12), fg=T.ACCENT,
                   size_hint=(None, None), size=(dp(86), dp(34)), font_size="13sp")
        btn.pos_hint = {"center_y": 0.5}

        def tap(b):
            if b.text != "Точно?":
                b.text = "Точно?"
                b.bg, b.fg = T.ACCENT, T.WHITE
                return
            app = App.get_running_app()
            app.store.delete(sh)
            app.after_data_change()
            self.on_change()
            self.build()
        btn.bind(on_release=tap)
        row.add_widget(btn)
        wrap = BoxLayout(size_hint_y=None, height=dp(62), padding=(0, dp(3)))
        wrap.add_widget(row)
        return wrap


# ---------------- вкладка целиком ----------------

class CalendarScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="calendar", **kw)
        self.sm = ScreenManager(transition=SlideTransition(duration=0.22))
        self.sm.parent_screen = self
        self.year_view = YearView()
        self.month_view = MonthView()
        self.sm.add_widget(self.year_view)
        self.sm.add_widget(self.month_view)
        self.add_widget(self.sm)

    def refresh(self):
        app = App.get_running_app()
        now = app.clock.now()
        self.year_view.refresh(app.store.day_map(now), now.date())
        if self.sm.current == "month":
            self.month_view.refresh()

    def on_pre_enter(self, *_):
        self.refresh()

    def open_month(self, y, m):
        self.month_view.show(y, m)
        self.sm.transition.direction = "left"
        self.sm.current = "month"

    def show_year(self):
        self.sm.transition.direction = "right"
        self.sm.current = "year"
        Clock.schedule_once(lambda *_: self.year_view.scroll_to_year(self.month_view.year), 0)

    def back(self) -> bool:
        if self.sm.current == "month":
            self.show_year()
            return True
        return False
