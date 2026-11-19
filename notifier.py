"""Уведомления. На Android — нативные (через pyjnius), на ПК — колбэк в UI."""
import os

IS_ANDROID = "ANDROID_PRIVATE" in os.environ or "ANDROID_ARGUMENT" in os.environ
CHANNEL_ID = "shift_alerts"
PACKAGE = "org.shiftapp.shifttracker"
SERVICE_CLASS = PACKAGE + ".ServiceWatcher"

desktop_handler = None  # функция(title, text) — ставит отладочный UI


def _context():
    from jnius import autoclass
    if os.environ.get("PYTHON_SERVICE_ARGUMENT") is not None:
        return autoclass("org.kivy.android.PythonService").mService
    return autoclass("org.kivy.android.PythonActivity").mActivity


def send(title: str, text: str, nid: int = 1):
    if not IS_ANDROID:
        if desktop_handler:
            desktop_handler(title, text)
        else:
            print(f"[notify] {title}: {text}")
        return
    try:
        _send_android(title, text, nid)
    except Exception as e:  # уведомление не должно ронять приложение
        print("notify failed:", e)


def _send_android(title, text, nid):
    from jnius import autoclass, cast
    String = autoclass("java.lang.String")
    ctx = _context()
    Context = autoclass("android.content.Context")
    sdk = autoclass("android.os.Build$VERSION").SDK_INT
    NM = autoclass("android.app.NotificationManager")
    nm = cast("android.app.NotificationManager",
              ctx.getSystemService(Context.NOTIFICATION_SERVICE))
    Builder = autoclass("android.app.Notification$Builder")
    if sdk >= 26:
        Channel = autoclass("android.app.NotificationChannel")
        ch = Channel(CHANNEL_ID, String("Напоминания о смене"), NM.IMPORTANCE_HIGH)
        nm.createNotificationChannel(ch)
        b = Builder(ctx, CHANNEL_ID)
    else:
        b = Builder(ctx)
    b.setSmallIcon(ctx.getApplicationInfo().icon)
    b.setContentTitle(String(title))
    b.setContentText(String(text))
    b.setAutoCancel(True)
    Intent = autoclass("android.content.Intent")
    PI = autoclass("android.app.PendingIntent")
    intent = Intent(ctx, autoclass("org.kivy.android.PythonActivity"))
    intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
    flags = PI.FLAG_UPDATE_CURRENT | (PI.FLAG_IMMUTABLE if sdk >= 23 else 0)
    b.setContentIntent(PI.getActivity(ctx, 0, intent, flags))
    nm.notify(nid, b.build())


def request_permission():
    if not IS_ANDROID:
        return
    try:
        from android.permissions import request_permissions
        request_permissions(["android.permission.POST_NOTIFICATIONS"])
    except Exception as e:
        print("permission request failed:", e)


def start_watcher(data_folder: str):
    """Фоновый сервис: шлёт уведомления 8/12 ч, даже если приложение закрыто."""
    if not IS_ANDROID:
        return
    try:
        import json
        from jnius import autoclass
        act = autoclass("org.kivy.android.PythonActivity").mActivity
        autoclass(SERVICE_CLASS).start(act, "", "Смена идёт",
                                       "Напомню после 8 и 12 часов",
                                       json.dumps({"data": data_folder}))
    except Exception as e:
        print("service start failed:", e)


def stop_watcher():
    if not IS_ANDROID:
        return
    try:
        from jnius import autoclass
        act = autoclass("org.kivy.android.PythonActivity").mActivity
        autoclass(SERVICE_CLASS).stop(act)
    except Exception as e:
        print("service stop failed:", e)
