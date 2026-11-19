"""Смена — учёт рабочего времени.

    python main.py           обычный режим
    python main.py --debug   отладка: сдвиг времени, тестовые данные
"""
import os
import sys

DEBUG = "--debug" in sys.argv
if DEBUG:
    sys.argv.remove("--debug")
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_LOG_MODE", "PYTHON" if DEBUG else "KIVY")

from kivy.config import Config  # noqa: E402
from kivy.utils import platform  # noqa: E402

if platform not in ("android", "ios"):
    Config.set("graphics", "width", "700" if DEBUG else "400")
    Config.set("graphics", "height", "820")
    Config.set("graphics", "resizable", "1")
Config.set("input", "mouse", "mouse,multitouch_on_demand")
Config.set("kivy", "exit_on_escape", "0")

from kivy.animation import Animation  # noqa: E402
from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.metrics import dp  # noqa: E402
from kivy.uix.boxlayout import BoxLayout  # noqa: E402
from kivy.uix.floatlayout import FloatLayout  # noqa: E402
from kivy.uix.screenmanager import FadeTransition, ScreenManager  # noqa: E402

import notifier  # noqa: E402
from core.clock import AppClock  # noqa: E402
from core.model import Store, alert_text, hhmm  # noqa: E402
from core.ru import num  # noqa: E402
from ui import theme as T  # noqa: E402
from ui.calendar import CalendarScreen  # noqa: E402
from ui.home import HomeScreen  # noqa: E402
from ui.settings import Onboarding, SettingsScreen  # noqa: E402
from ui.widgets import Card, Lbl, TabBar  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


class ShiftApp(App):
    title = "Смена"

    def build(self):
        self.clock = AppClock()
        folder = os.path.join(HERE, "debug_data") if DEBUG else self.user_data_dir
        self.store = Store(folder)
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self.on_key)

        self.phone = FloatLayout()
        self.theme_name = T.resolve(self.store.settings.theme)
        T.apply(self.theme_name)
        self.build_ui()

        self.debug = None
        if DEBUG:
            from ui.debug import DebugPanel
            root = BoxLayout()
            self.phone.size_hint_x = None
            self.phone.width = dp(400)
            root.add_widget(self.phone)
            self.debug = DebugPanel()
            root.add_widget(self.debug)
            notifier.desktop_handler = self.on_desktop_notify
        else:
            root = self.phone

        self._ticks = 0
        Clock.schedule_interval(self.tick, 1)
        Clock.schedule_once(lambda *_: self.start(), 0)
        return root

    # ---------- интерфейс и тема ----------
    def build_ui(self, tab="home"):
        Window.clearcolor = T.BG
        self.phone.clear_widgets()
        col = BoxLayout(orientation="vertical")
        self.sm = ScreenManager(transition=FadeTransition(duration=0.12))
        self.home = HomeScreen()
        self.cal = CalendarScreen()
        self.settings_screen = SettingsScreen()
        for s in (self.home, self.cal, self.settings_screen):
            self.sm.add_widget(s)
        self.tabs = TabBar(on_select=self.go)
        col.add_widget(self.sm)
        col.add_widget(self.tabs)
        self.phone.add_widget(col)
        self.sm.transition = FadeTransition(duration=0)
        self.go(tab)
        self.sm.transition = FadeTransition(duration=0.12)
        self.home.refresh()
        self.style_status_bar()

    def set_theme(self, setting):
        """setting: system / light / dark"""
        self.store.settings.theme = setting
        self.store.save()
        self.update_theme()

    def update_theme(self):
        name = T.resolve(self.store.settings.theme)
        if name == self.theme_name:
            return
        self.theme_name = name
        T.apply(name)
        onboarding = any(w.__class__.__name__ == "Onboarding" for w in self.phone.children)
        self.build_ui(tab=self.sm.current)
        if onboarding:
            self.show_onboarding()

    def style_status_bar(self):
        """Цвет строки состояния Android под тему."""
        if platform != "android":
            return
        try:
            from android.runnable import run_on_ui_thread
            from jnius import autoclass
            Color = autoclass("android.graphics.Color")
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            bg, dark = "#" + T.hex_of(T.BG), T.DARK

            @run_on_ui_thread
            def apply():
                win = act.getWindow()
                win.setStatusBarColor(Color.parseColor(bg))
                win.setNavigationBarColor(Color.parseColor(bg))
                view = win.getDecorView()
                flags = view.getSystemUiVisibility()
                light_bar = 0x2000 | 0x10  # LIGHT_STATUS_BAR | LIGHT_NAVIGATION_BAR
                view.setSystemUiVisibility(flags & ~light_bar if dark else flags | light_bar)
            apply()
        except Exception as e:
            print("status bar:", e)

    def start(self):
        self.home.refresh()
        self.tick(0)
        if not self.store.settings.onboarded:
            self.show_onboarding()
        elif self.store.open_start and self.store.settings.notify:
            notifier.start_watcher(self.store.folder)

    def show_onboarding(self):
        Onboarding().open()

    # ---------- навигация ----------
    def go(self, name):
        self.tabs.select(name)
        if name == "calendar" and self.sm.current == "calendar":
            self.cal.show_year()
        self.sm.current = name

    def on_key(self, _win, key, *_):
        if key == 27:  # Back на Android / Esc
            if self.sm.current == "calendar" and self.cal.back():
                return True
            if self.sm.current != "home":
                self.go("home")
                return True
            return False
        return False

    # ---------- смены ----------
    def toggle_shift(self):
        now = self.clock.now()
        if self.store.open_start is None:
            self.store.check_in(now)
            self.toast(f"Смена началась в {now:%H:%M}")
            if self.store.settings.notify:
                notifier.start_watcher(self.store.folder)
        else:
            sh = self.store.check_out(now)
            notifier.stop_watcher()
            m = sh.minutes(now)
            self.toast(f"Отработано {hhmm(m)}  ({num(m)} мин)")
        self.after_data_change()

    def set_notify(self, value):
        self.store.settings.notify = value
        self.store.save()
        if value:
            notifier.request_permission()
            if self.store.open_start:
                notifier.start_watcher(self.store.folder)
        else:
            notifier.stop_watcher()

    def after_data_change(self):
        self.home.refresh()
        if self.sm.current == "calendar":
            self.cal.refresh()
        if self.sm.current == "settings":
            self.settings_screen.refresh()
        self.check_alerts()
        if self.debug:
            self.debug.tick()

    # ---------- таймер ----------
    def tick(self, _dt):
        self._ticks += 1
        if self.sm.current == "home":
            self.home.refresh()
        if self.debug:
            self.debug.tick()
        if DEBUG or self._ticks % 10 == 0:
            self.check_alerts()
        if self.store.settings.theme == "system" and self._ticks % 3 == 0:
            self.update_theme()  # тему телефона могли переключить

    def check_alerts(self):
        due = self.store.due_alerts(self.clock.now())
        for h in due:
            notifier.send(*alert_text(h, self.store.open_start), nid=100 + h)
            for hh in (8, 12):
                if hh <= h:
                    self.store.mark_notified(self.store.open_start, hh)

    def on_desktop_notify(self, title, text):
        self.toast(f"{title} — {text}")
        if self.debug:
            self.debug.notified(title, text)

    # ---------- тост ----------
    def toast(self, text):
        card = Card(bg=list(T.TOAST), radius=dp(14), padding=(dp(16), dp(12)),
                    size_hint=(None, None), opacity=0)
        lbl = Lbl(text=text, color=T.WHITE, halign="center", font_size="15sp")
        card.add_widget(lbl)
        card.width = self.phone.width - dp(48)
        lbl.bind(height=lambda *_: setattr(card, "height", lbl.height + dp(24)))
        card.height = dp(48)
        card.pos_hint = {"center_x": 0.5, "y": 0.11}
        self.phone.add_widget(card)
        a = (Animation(opacity=1, d=0.18) + Animation(d=2.4)
             + Animation(opacity=0, d=0.3))
        a.bind(on_complete=lambda *_: self.phone.remove_widget(card))
        a.start(card)

    # ---------- жизненный цикл Android ----------
    def on_pause(self):
        return True

    def on_resume(self):
        self.store.load()
        self.update_theme()
        self.after_data_change()


if __name__ == "__main__":
    ShiftApp().run()
