"""Цвета приложения. Значения меняются при смене темы (apply), поэтому
везде обращаемся к ним как T.BG, T.TEXT и т.д., а не копируем."""
import os

from kivy.utils import get_color_from_hex as _c

PALETTES = {
    "light": dict(BG="#F2F2F7", CARD="#FFFFFF", TEXT="#1C1C1E", MUTED="#8E8E93",
                  LINE="#E5E5EA", ACCENT="#FF3B30", GREEN="#34C759", NIGHT="#5E5CE6",
                  TOAST="#1C1C1EEB", KNOB="#FFFFFF", SEG="#FFFFFF"),
    "dark": dict(BG="#000000", CARD="#1C1C1E", TEXT="#F2F2F7", MUTED="#8E8E93",
                 LINE="#38383A", ACCENT="#FF453A", GREEN="#30D158", NIGHT="#7D7AFF",
                 TOAST="#3A3A3CF0", KNOB="#F2F2F7", SEG="#48484A"),
}
WHITE = [1, 1, 1, 1]
DARK = False

BG = CARD = TEXT = MUTED = LINE = ACCENT = GREEN = NIGHT = TOAST = KNOB = SEG = None


def apply(name: str):
    """Включить палитру 'light' или 'dark'."""
    global DARK
    DARK = name == "dark"
    for k, v in PALETTES[name].items():
        globals()[k] = _c(v)


apply("light")


def soft(c, a=0.14):
    if DARK:
        a = min(1.0, a * 1.6)  # на тёмном фоне оттенки нужны поярче
    return [c[0], c[1], c[2], a]


def mix(a, b, p):
    return [x + (y - x) * p for x, y in zip(a, b)]


def hex_of(c):
    return "".join(f"{int(round(x * 255)):02X}" for x in c[:3])


# ---------- какая тема стоит в системе ----------

debug_system_override = None  # 'light'/'dark' — имитация системной темы в отладке


def system_theme() -> str:
    if debug_system_override:
        return debug_system_override
    if "ANDROID_PRIVATE" in os.environ or "ANDROID_ARGUMENT" in os.environ:
        try:
            from jnius import autoclass
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            mode = act.getResources().getConfiguration().uiMode & 0x30
            return "dark" if mode == 0x20 else "light"  # UI_MODE_NIGHT_YES
        except Exception:
            return "light"
    if os.name == "nt":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if val else "dark"
        except OSError:
            return "light"
    return "light"


def resolve(setting: str) -> str:
    return system_theme() if setting == "system" else setting
