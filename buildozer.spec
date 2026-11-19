[app]
title = Смена
package.name = shifttracker
package.domain = org.shiftapp
source.dir = .
source.include_exts = py,png,json
source.exclude_dirs = tests,.venv,debug_data,.github,bin,.buildozer,.git
source.exclude_patterns = p4a_hook.py
version = 1.1

requirements = python3,kivy==2.3.0,pyjnius,android
orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png
android.presplash_color = #F2F2F7

# фоновый сервис уведомлений 8/12 ч (класс org.shiftapp.shifttracker.ServiceWatcher)
services = Watcher:service/main.py:foreground

android.permissions = POST_NOTIFICATIONS, FOREGROUND_SERVICE, FOREGROUND_SERVICE_SPECIAL_USE
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.ndk = 25b
android.accept_sdk_license = True
android.allow_backup = True

# стабильная версия python-for-android (Python 3.11)
p4a.branch = v2024.01.21
# API 35: свежий Gradle, тип службы, отказ от edge-to-edge (см. p4a_hook.py)
p4a.hook = p4a_hook.py

[buildozer]
log_level = 2
warn_on_root = 0
