from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

Builder.load_string("""
#:import T ui.theme
#:import dp kivy.metrics.dp

<SectionLbl@Lbl>:
    color: T.MUTED
    font_size: '13sp'
    padding: dp(16), dp(6)

<RateRow>:
    size_hint_y: None
    height: dp(56)
    Card:
        height: dp(56)
        padding: dp(16), 0
        spacing: dp(6)
        Lbl:
            text: 'Ставка в час'
            size_hint_y: 1
        Field:
            id: rate
            hint_text: '0'
            input_type: 'number'
            on_focus: if not self.focus: root.commit()
            on_text_validate: root.commit()
        Lbl:
            text: '€'
            size_hint_y: 1
            size_hint_x: None
            width: dp(16)
            color: T.MUTED

<NotifyRow>:
    size_hint_y: None
    height: dp(66)
    Card:
        height: dp(66)
        padding: dp(16), 0
        BoxLayout:
            orientation: 'vertical'
            padding: 0, dp(12)
            Lbl:
                text: 'Напоминания'
            Lbl:
                text: 'После 8 и 12 часов смены'
                color: T.MUTED
                font_size: '13sp'
        AnchorLayout:
            size_hint_x: None
            width: dp(56)
            ToggleSwitch:
                id: sw
                on_active: root.changed(self.active)

<SettingsScreen>:
    name: 'settings'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(16), dp(22), dp(16), dp(16)
        spacing: dp(6)
        Lbl:
            text: 'Настройки'
            bold: True
            font_size: '32sp'
            padding: dp(4), 0, 0, dp(10)
        SectionLbl:
            text: 'ЗАРПЛАТА'
        RateRow:
            id: rate
        SectionLbl:
            text: 'Нужна, чтобы считать заработок за день и месяц'
        Widget:
            size_hint_y: None
            height: dp(10)
        SectionLbl:
            text: 'УВЕДОМЛЕНИЯ'
        NotifyRow:
            id: notify
        Widget:
            size_hint_y: None
            height: dp(10)
        SectionLbl:
            text: 'ОФОРМЛЕНИЕ'
        Card:
            id: theme_box
            height: dp(48)
            padding: dp(4)
        SectionLbl:
            id: theme_hint
        Widget:
            size_hint_y: None
            height: dp(4)
        SectionLbl:
            text: 'ДАННЫЕ'
        Card:
            height: dp(74)
            padding: dp(16), dp(12)
            orientation: 'vertical'
            Lbl:
                text: 'Хранятся только на этом телефоне'
            Lbl:
                id: path
                color: T.MUTED
                font_size: '11sp'
        Widget
        Lbl:
            text: 'Смена · версия 1.0'
            halign: 'center'
            color: T.MUTED
            font_size: '12sp'

<Onboarding>:
    canvas.before:
        Color:
            rgba: T.BG
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        pos: root.pos
        size: root.size
        padding: dp(20), dp(40), dp(20), dp(28)
        spacing: dp(8)
        Widget:
            size_hint_y: 0.3
        ClockLogo:
            size_hint: None, None
            size: dp(104), dp(104)
            pos_hint: {'center_x': 0.5}
        Lbl:
            text: 'Смена'
            bold: True
            font_size: '40sp'
            halign: 'center'
        Lbl:
            text: 'Учёт рабочего времени в одно касание.\\nДве настройки — и можно начинать.'
            color: T.MUTED
            halign: 'center'
            font_size: '15sp'
        Widget:
            size_hint_y: 0.4
        SectionLbl:
            text: 'СКОЛЬКО ТЕБЕ ПЛАТЯТ В ЧАС?'
        RateRow:
            id: rate
        Widget:
            size_hint_y: None
            height: dp(8)
        SectionLbl:
            text: 'ПРИСЫЛАТЬ УВЕДОМЛЕНИЯ?'
        NotifyRow:
            id: notify
        Widget
        Pill:
            text: 'Начать'
            size_hint_y: None
            height: dp(54)
            radius: dp(16)
            font_size: '17sp'
            on_release: root.finish()
""")


class RateRow(BoxLayout):
    def load(self):
        r = App.get_running_app().store.settings.rate
        self.ids.rate.text = (f"{r:.2f}".rstrip("0").rstrip(".")) if r else ""

    def commit(self):
        app = App.get_running_app()
        try:
            app.store.settings.rate = max(0.0, float(self.ids.rate.text or 0))
        except ValueError:
            return
        app.store.save()
        app.after_data_change()


class NotifyRow(BoxLayout):
    _loading = False

    def load(self):
        self._loading = True
        sw = self.ids.sw
        sw.active = App.get_running_app().store.settings.notify
        sw.p = 1 if sw.active else 0
        self._loading = False

    def changed(self, value):
        if self._loading:
            return
        App.get_running_app().set_notify(value)


class SettingsScreen(Screen):
    def on_kv_post(self, *_):
        from ui.widgets import Segmented
        app = App.get_running_app()
        self.seg = Segmented(options=[("system", "Как в системе"), ("light", "Светлая"),
                                      ("dark", "Тёмная")],
                             on_change=lambda v: Clock.schedule_once(lambda *_: app.set_theme(v), 0.22))
        self.ids.theme_box.add_widget(self.seg)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        from ui import theme as T
        app = App.get_running_app()
        self.seg.set(app.store.settings.theme)
        sys_name = "тёмная" if T.system_theme() == "dark" else "светлая"
        self.ids.theme_hint.text = f"Сейчас в системе: {sys_name} тема"
        self.ids.rate.load()
        self.ids.notify.load()
        self.ids.path.text = App.get_running_app().store.path


class Onboarding(FloatLayout):
    """Экран первого запуска (поверх приложения)."""
    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        return True  # не пропускать касания под экран

    def open(self):
        App.get_running_app().phone.add_widget(self)
        self.ids.rate.load()
        self.ids.notify.load()

    def finish(self):
        app = App.get_running_app()
        self.ids.rate.commit()
        app.store.settings.onboarded = True
        app.store.save()
        if app.store.settings.notify:
            import notifier
            notifier.request_permission()
        if self.parent:
            self.parent.remove_widget(self)
        app.after_data_change()
