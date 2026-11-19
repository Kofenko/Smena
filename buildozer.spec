[app]
title = Смена
package.name = shifttracker
package.domain = org.shiftapp
source.dir = .
source.include_exts = py,png,json
source.exclude_dirs = tests,.venv,debug_data,.github,bin,.buildozer,.git
version = 1.0

requirements = python3,kivy==2.3.1,pyjnius,android
orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png
android.presplash_color = #F2F2F7

# фоновый сервис уведомлений 8/12 ч (класс org.shiftapp.shifttracker.ServiceWatcher)
services = Watcher:service/main.py:foreground

android.permissions = POST_NOTIFICATIONS, FOREGROUND_SERVICE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 0
