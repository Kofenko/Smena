"""Хук python-for-android: правки проекта перед сборкой Gradle.

Нужен, чтобы собрать приложение под Android 15 (API 35) на стабильном p4a:
  * свежий Android Gradle Plugin (старый 8.1 не умеет compileSdk 35);
  * тип фоновой службы specialUse (обязателен с API 34);
  * отказ от принудительного edge-to-edge Android 15, чтобы интерфейс
    не залезал под статус-бар и панель навигации.
"""
import os
import re

AGP = "8.7.3"
GRADLE = "8.9"
SERVICE = "org.shiftapp.shifttracker.ServiceWatcher"


def _edit(path, fn):
    with open(path, encoding="utf-8") as f:
        old = f.read()
    new = fn(old)
    if new != old:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
    print(f"[p4a_hook] {path}: {'изменён' if new != old else 'без изменений'}")


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _manifest(x):
    if "FOREGROUND_SERVICE_SPECIAL_USE" not in x:
        x = x.replace(
            "<application",
            '<uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />\n'
            "    <application", 1)
    x = re.sub(
        r'(<service android:name="' + re.escape(SERVICE) + r'"[^>]*?)\s*/>',
        r'\1 android:foregroundServiceType="specialUse">'
        r'<property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"'
        r' android:value="Work shift timer and reminders" /></service>',
        x, count=1)
    # тема приложения -> своя (с отказом от edge-to-edge на API 35)
    x = re.sub(r'android:theme="@android:style/Theme\.NoTitleBar[^"]*"',
               'android:theme="@style/SmenaTheme"', x)
    return x


def before_apk_assemble(toolchain):
    # cwd = папка дистрибутива p4a
    _edit("build.gradle", lambda s: re.sub(
        r"com\.android\.tools\.build:gradle:[\d.]+",
        f"com.android.tools.build:gradle:{AGP}", s))
    _edit(os.path.join("gradle", "wrapper", "gradle-wrapper.properties"),
          lambda s: re.sub(r"gradle-[\d.]+-(all|bin)\.zip",
                           f"gradle-{GRADLE}-all.zip", s))
    _edit(os.path.join("src", "main", "AndroidManifest.xml"), _manifest)

    res = os.path.join("src", "main", "res")
    _write(os.path.join(res, "values", "smena_theme.xml"),
           '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
           '    <style name="SmenaTheme" parent="@android:style/Theme.NoTitleBar" />\n'
           '</resources>\n')
    _write(os.path.join(res, "values-v35", "smena_theme.xml"),
           '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
           '    <style name="SmenaTheme" parent="@android:style/Theme.NoTitleBar">\n'
           '        <item name="android:windowOptOutEdgeToEdgeEnforcement">true</item>\n'
           '    </style>\n</resources>\n')
