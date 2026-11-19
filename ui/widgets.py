"""Базовые виджеты в минималистичном стиле."""
import math

from kivy.animation import Animation
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Line, Rectangle
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             StringProperty)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from ui import theme as T

Builder.load_string("""
#:import T ui.theme
#:import dp kivy.metrics.dp

<Lbl>:
    color: T.TEXT
    size_hint_y: None
    height: self.texture_size[1]
    text_size: self.width, None
    halign: 'left'
    font_size: '16sp'

<Card>:
    size_hint_y: None
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius]

<Pill>:
    color: self.fg
    bold: True
    font_size: '15sp'
    canvas.before:
        Color:
            rgba: self.bg[:3] + [self.bg[3] * (0.55 if self.state == 'down' else 1)]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius or self.height / 2]

<Chip>:
    size_hint: None, None
    height: dp(30)
    width: self.texture_size[0] + dp(24) if self.text else 0
    opacity: 1 if self.text else 0
    font_size: '14sp'
    bold: True
    color: self.fg
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]

<BigButton>:
    canvas:
        Color:
            rgba: T.soft(self.tone, 0.12)
        Ellipse:
            pos: self.center_x - self.d / 2, self.center_y - self.d / 2
            size: self.d, self.d
        Color:
            rgba: self.tone
        Ellipse:
            pos: self.center_x - self.d * 0.4 * self.k, self.center_y - self.d * 0.4 * self.k
            size: self.d * 0.8 * self.k, self.d * 0.8 * self.k
    Label:
        text: root.text
        bold: True
        font_size: '28sp'
        color: 1, 1, 1, 1
        size: self.texture_size
        center: root.center

<ToggleSwitch>:
    size_hint: None, None
    size: dp(51), dp(31)
    canvas:
        Color:
            rgba: T.mix(T.LINE, T.GREEN, self.p)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]
        Color:
            rgba: 0, 0, 0, 0.08
        Ellipse:
            pos: self.x + dp(2) + self.p * (self.width - self.height), self.y + dp(1)
            size: self.height - dp(4), self.height - dp(4)
        Color:
            rgba: T.KNOB
        Ellipse:
            pos: self.x + dp(2) + self.p * (self.width - self.height), self.y + dp(2)
            size: self.height - dp(4), self.height - dp(4)

<Field>:
    background_normal: ''
    background_active: ''
    background_color: 0, 0, 0, 0
    foreground_color: T.TEXT
    cursor_color: T.ACCENT
    hint_text_color: T.MUTED
    font_size: '17sp'
    multiline: False
    write_tab: False
    halign: 'right'
    padding: 0, (self.height - self.line_height) / 2
""")


class Lbl(Label):
    pass


# Цвета по умолчанию берутся в момент создания виджета — так они
# соответствуют текущей теме.

class Card(BoxLayout):
    bg = ListProperty([1, 1, 1, 1])
    radius = NumericProperty(dp(16))

    def __init__(self, **kw):
        kw.setdefault("bg", list(T.CARD))
        super().__init__(**kw)


class Pill(ButtonBehavior, Label):
    bg = ListProperty([1, 1, 1, 1])
    fg = ListProperty([1, 1, 1, 1])
    radius = NumericProperty(0)

    def __init__(self, **kw):
        kw.setdefault("bg", list(T.ACCENT))
        kw.setdefault("fg", list(T.WHITE))
        super().__init__(**kw)


class Chip(Label):
    bg = ListProperty([1, 1, 1, 1])
    fg = ListProperty([1, 1, 1, 1])

    def __init__(self, **kw):
        kw.setdefault("bg", T.soft(T.ACCENT))
        kw.setdefault("fg", list(T.ACCENT))
        super().__init__(**kw)


class BigButton(ButtonBehavior, Widget):
    text = StringProperty("")
    tone = ListProperty([1, 1, 1, 1])
    k = NumericProperty(1)
    d = NumericProperty(dp(220))

    def __init__(self, **kw):
        kw.setdefault("tone", list(T.GREEN))
        super().__init__(**kw)

    def on_press(self):
        Animation.cancel_all(self, "k")
        Animation(k=0.93, d=0.08).start(self)

    def on_release(self):
        Animation(k=1, d=0.25, t="out_back").start(self)

    def set_tone(self, color):
        Animation(tone=list(color), d=0.25).start(self)


class ToggleSwitch(ButtonBehavior, Widget):
    active = BooleanProperty(False)
    p = NumericProperty(0)

    def on_kv_post(self, *_):
        self.p = 1 if self.active else 0

    def on_release(self):
        self.active = not self.active

    def on_active(self, *_):
        Animation(p=1 if self.active else 0, d=0.18, t="out_quad").start(self)


class Field(TextInput):
    def insert_text(self, substring, from_undo=False):
        out = ""
        for ch in substring:
            if ch in ",.":
                ch = "."
                if "." in self.text or "." in out:
                    continue
            elif not ch.isdigit():
                continue
            out += ch
        return super().insert_text(out, from_undo=from_undo)


class ClockLogo(Widget):
    """Логотип: красный круг с циферблатом."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        from kivy.graphics import Ellipse
        self.canvas.clear()
        d = min(self.size)
        cx, cy = self.center
        with self.canvas:
            Color(*T.soft(T.ACCENT, 0.14))
            Ellipse(pos=(cx - d / 2, cy - d / 2), size=(d, d))
            Color(*T.ACCENT)
            r = d * 0.38
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            Color(1, 1, 1, 1)
            Line(circle=(cx, cy, r * 0.62), width=dp(2.2))
            Line(points=[cx, cy + r * 0.42, cx, cy, cx + r * 0.3, cy - r * 0.2],
                 width=dp(2.4), cap="round", joint="round")


class Segmented(Widget):
    """Переключатель на несколько положений в стиле iOS."""
    value = StringProperty("")
    pos_k = NumericProperty(0)

    def __init__(self, options=(), on_change=None, **kw):
        super().__init__(**kw)
        self.options = list(options)   # [(значение, подпись)]
        self.on_change = on_change
        self.bind(pos=self.draw, size=self.draw, pos_k=self.draw)

    def index(self):
        vals = [v for v, _ in self.options]
        return vals.index(self.value) if self.value in vals else 0

    def on_value(self, *_):
        Animation.cancel_all(self, "pos_k")
        Animation(pos_k=self.index(), d=0.2, t="out_quad").start(self)
        self.draw()

    def set(self, value):
        self.value = value
        self.pos_k = self.index()

    def draw(self, *_):
        from kivy.graphics import Rectangle, RoundedRectangle
        self.canvas.clear()
        n = len(self.options)
        if not n:
            return
        sw = self.width / n
        with self.canvas:
            Color(*T.soft(T.TEXT, 0.07))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(9)])
            Color(*T.SEG)
            RoundedRectangle(pos=(self.x + dp(2) + sw * self.pos_k, self.y + dp(2)),
                             size=(sw - dp(4), self.height - dp(4)), radius=[dp(7)])
            for i, (v, label) in enumerate(self.options):
                sel = v == self.value
                t = text_texture(label, sp(14), T.TEXT, bold=sel)
                Color(1, 1, 1, 1)
                Rectangle(texture=t, size=t.size,
                          pos=(self.x + sw * (i + 0.5) - t.width / 2, self.center_y - t.height / 2))

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.options and touch.grab_current is None:
            i = min(len(self.options) - 1, int((touch.x - self.x) / (self.width / len(self.options))))
            v = self.options[i][0]
            if v != self.value:
                self.value = v
                if self.on_change:
                    self.on_change(v)
            return True
        return super().on_touch_up(touch)


# ---------- нижняя панель вкладок ----------

class TabItem(ButtonBehavior, Widget):
    text = StringProperty("")
    icon = StringProperty("clock")
    active = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.draw, size=self.draw, active=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        col = T.ACCENT if self.active else T.MUTED
        cx, cy = self.center_x, self.y + self.height * 0.62
        w = dp(1.8)
        with self.canvas:
            Color(*col)
            if self.icon == "clock":
                r = dp(10)
                Line(circle=(cx, cy, r), width=w)
                Line(points=[cx, cy + r * 0.6, cx, cy, cx + r * 0.45, cy - r * 0.3], width=w)
            elif self.icon == "cal":
                a, b = dp(10), dp(9)
                Line(rounded_rectangle=(cx - a, cy - b, 2 * a, 2 * b, dp(3)), width=w)
                Line(points=[cx - a, cy + b * 0.35, cx + a, cy + b * 0.35], width=w)
                Line(points=[cx - a * 0.45, cy + b, cx - a * 0.45, cy + b + dp(3)], width=w)
                Line(points=[cx + a * 0.45, cy + b, cx + a * 0.45, cy + b + dp(3)], width=w)
            else:
                Line(circle=(cx, cy, dp(4)), width=w)
                Line(circle=(cx, cy, dp(8)), width=w)
                for i in range(8):
                    ang = i * math.pi / 4
                    Line(points=[cx + math.cos(ang) * dp(8), cy + math.sin(ang) * dp(8),
                                 cx + math.cos(ang) * dp(11), cy + math.sin(ang) * dp(11)],
                         width=w, cap="round")
            t = text_texture(self.text, sp(11), col, bold=self.active)
            from kivy.graphics import Rectangle
            Rectangle(texture=t, size=t.size,
                      pos=(cx - t.width / 2, self.y + self.height * 0.14))


class TabBar(BoxLayout):
    def __init__(self, on_select, **kw):
        super().__init__(size_hint_y=None, height=dp(62), **kw)
        self.items = {}
        for name, text, icon in (("home", "Смена", "clock"),
                                 ("calendar", "Календарь", "cal"),
                                 ("settings", "Настройки", "gear")):
            it = TabItem(text=text, icon=icon)
            it.bind(on_release=lambda _, n=name: on_select(n))
            self.items[name] = it
            self.add_widget(it)
        with self.canvas.before:
            Color(*T.CARD)
            from kivy.graphics import Rectangle
            self._bg = Rectangle()
            Color(*T.LINE)
            self._ln = Rectangle()
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size
        self._ln.pos = (self.x, self.top - 1)
        self._ln.size = (self.width, 1)

    def select(self, name):
        for n, it in self.items.items():
            it.active = n == name


# ---------- кэш текстур для быстрых календарей ----------

_cache = {}


def text_texture(text, size, color, bold=False):
    key = (text, round(size, 1), tuple(round(c, 3) for c in color), bold)
    t = _cache.get(key)
    if t is None:
        lbl = CoreLabel(text=text, font_size=size, color=list(color), bold=bold)
        lbl.refresh()
        t = _cache[key] = lbl.texture
    return t
